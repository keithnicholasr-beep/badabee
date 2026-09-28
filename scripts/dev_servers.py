"""Windows local-development launcher; uses only Python's standard library."""
import argparse
import ctypes
from ctypes import wintypes
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time
import urllib.request
import webbrowser

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / '.dev-runtime'
STATE = RUNTIME / 'servers.json'
PYTHON = ROOT / 'backend' / '.venv' / 'Scripts' / 'python.exe'
VITE = ROOT / 'swastya' / 'node_modules' / 'vite' / 'bin' / 'vite.js'
kernel = ctypes.WinDLL('kernel32', use_last_error=True)
kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
kernel.OpenProcess.restype = wintypes.HANDLE
kernel.CloseHandle.argtypes = [wintypes.HANDLE]
kernel.GetProcessTimes.argtypes = [wintypes.HANDLE] + [ctypes.POINTER(wintypes.FILETIME)] * 4
kernel.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
kernel.TerminateProcess.argtypes = [wintypes.HANDLE, wintypes.UINT]
kernel.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
kernel.CreateToolhelp32Snapshot.restype = wintypes.HANDLE


class ProcessEntry(ctypes.Structure):
    _fields_ = [('dwSize', wintypes.DWORD), ('cntUsage', wintypes.DWORD),
                ('th32ProcessID', wintypes.DWORD), ('th32DefaultHeapID', ctypes.c_size_t),
                ('th32ModuleID', wintypes.DWORD), ('cntThreads', wintypes.DWORD),
                ('th32ParentProcessID', wintypes.DWORD), ('pcPriClassBase', wintypes.LONG),
                ('dwFlags', wintypes.DWORD), ('szExeFile', wintypes.WCHAR * 260)]


kernel.Process32FirstW.argtypes = [wintypes.HANDLE, ctypes.POINTER(ProcessEntry)]
kernel.Process32NextW.argtypes = [wintypes.HANDLE, ctypes.POINTER(ProcessEntry)]


def child_processes(parent):
    snapshot = kernel.CreateToolhelp32Snapshot(2, 0)
    if snapshot == ctypes.c_void_p(-1).value:
        raise OSError('Could not inspect the managed server process tree')
    try:
        entry = ProcessEntry()
        entry.dwSize = ctypes.sizeof(entry)
        found = kernel.Process32FirstW(snapshot, ctypes.byref(entry))
        children = []
        while found:
            if entry.th32ParentProcessID == parent['pid']:
                record = process_record(entry.th32ProcessID)
                if record and record['created'] >= parent['created']:
                    children.append(record)
            found = kernel.Process32NextW(snapshot, ctypes.byref(entry))
        return children
    finally:
        kernel.CloseHandle(snapshot)


def process_record(pid, expected=None, stop=False):
    # Compare executable and creation time, so a reused PID cannot stop another process.
    handle = kernel.OpenProcess(0x1000 | (0x0001 if stop else 0), False, pid)
    if not handle:
        return None
    try:
        times = [wintypes.FILETIME() for _ in range(4)]
        size = wintypes.DWORD(32768)
        path = ctypes.create_unicode_buffer(size.value)
        if not kernel.GetProcessTimes(handle, *(ctypes.byref(t) for t in times)):
            return None
        if not kernel.QueryFullProcessImageNameW(handle, 0, path, ctypes.byref(size)):
            return None
        result = {'pid': pid, 'executable': os.path.normcase(path.value),
                  'created': (times[0].dwHighDateTime << 32) | times[0].dwLowDateTime}
        if expected is not None and result != expected:
            return None
        if stop:
            # Windows venv launchers may create a child Python process. Stop the
            # verified server tree, not just the launcher, to avoid orphan servers.
            for child in child_processes(result):
                process_record(child['pid'], expected=child, stop=True)
            if not kernel.TerminateProcess(handle, 0):
                # A venv parent may exit automatically when its child stops.
                code = wintypes.DWORD()
                kernel.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
                if kernel.GetExitCodeProcess(handle, ctypes.byref(code)) and code.value != 259:
                    return result
                raise OSError('Could not stop a managed development server')
        return result
    finally:
        kernel.CloseHandle(handle)


def save(state):
    temporary = STATE.with_suffix('.tmp')
    temporary.write_text(json.dumps(state, indent=2), encoding='utf-8')
    temporary.replace(STATE)


def ready(name):
    urls = (['http://127.0.0.1:8000/health'] if name == 'backend'
            else ['http://127.0.0.1:5173/', 'http://localhost:5173/'])
    for url in urls:
        try:
            with urllib.request.urlopen(url, timeout=1) as response:
                content = response.read().decode('utf-8')
                if name == 'backend' and json.loads(content).get('status') == 'ok':
                    return True
                if name == 'frontend' and 'SWASTYA' in content:
                    return True
        except (OSError, ValueError):
            pass
    return False


def occupied(port):
    for host in ('127.0.0.1', '::1'):
        try:
            with socket.create_connection((host, port), timeout=0.3):
                return True
        except OSError:
            pass
    return False


def run(action, open_browser=True):
    RUNTIME.mkdir(exist_ok=True)
    node = shutil.which('node.exe')
    if action == 'check':
        if not PYTHON.is_file() or not VITE.is_file() or not node:
            raise RuntimeError('Missing Python environment, frontend dependencies, or Node.js.')
        print('Python, Node.js and Vite are available.')
        return

    lock_path = RUNTIME / 'launcher.lock'
    if lock_path.exists() and time.time() - lock_path.stat().st_mtime > 120:
        lock_path.unlink()
    try:
        lock_fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        return  # A previous double-click is still being handled.
    try:
        state = json.loads(STATE.read_text()) if STATE.exists() else {}
        if action == 'stop':
            for record in state.values():
                process_record(record['pid'], expected=record, stop=True)
            save({})
            return
        if not PYTHON.is_file() or not VITE.is_file() or not node:
            raise RuntimeError('Missing Python environment, Node.js or node_modules. Install the project dependencies first.')
        services = {
            'backend': ([str(PYTHON), '-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', '8000'], ROOT / 'backend', 8000),
            'frontend': ([node, str(VITE), '--configLoader', 'native', '--host', '127.0.0.1', '--port', '5173', '--strictPort'], ROOT / 'swastya', 5173),
        }
        for name, (command, cwd, port) in services.items():
            if ready(name):
                continue  # Reuse existing servers; do not take ownership of them.
            if occupied(port):
                raise RuntimeError(f'Port {port} is already in use. Close the old server and try again.')
            with (RUNTIME / f'{name}.log').open('a', encoding='utf-8') as log:
                log.write(f'\n--- Started {time.ctime()} ---\n')
                log.flush()
                process = subprocess.Popen(command, cwd=cwd, stdin=subprocess.DEVNULL,
                    stdout=log, stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW)
            record = process_record(process.pid)
            if not record:
                raise RuntimeError(f'{name} could not start. Check .dev-runtime/{name}.log.')
            state[name] = record
            save(state)
            deadline = time.monotonic() + 30
            while not ready(name):
                if process.poll() is not None or time.monotonic() >= deadline:
                    raise RuntimeError(f'{name} did not become ready. Check .dev-runtime/{name}.log.')
                time.sleep(0.3)
        if open_browser:
            webbrowser.open('http://localhost:5173/')
    finally:
        os.close(lock_fd)
        lock_path.unlink(missing_ok=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['start', 'stop', 'check'])
    parser.add_argument('--no-browser', action='store_true')
    parser.add_argument('--no-dialog', action='store_true')
    args = parser.parse_args()
    try:
        run(args.action, not args.no_browser)
    except Exception as error:
        RUNTIME.mkdir(exist_ok=True)
        with (RUNTIME / 'launcher.log').open('a', encoding='utf-8') as log:
            log.write(f'{time.ctime()}: {type(error).__name__}: {error}\n')
        if not args.no_dialog:
            ctypes.windll.user32.MessageBoxW(None, str(error), 'SWASTYA launcher', 0x10)
        if sys.stderr:
            print(str(error), file=sys.stderr)
        sys.exit(1)
