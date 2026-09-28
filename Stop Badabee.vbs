Option Explicit
Dim shell, files, root, python, script
Set shell = CreateObject("WScript.Shell")
Set files = CreateObject("Scripting.FileSystemObject")
root = files.GetParentFolderName(WScript.ScriptFullName)
python = root & "\backend\.venv\Scripts\pythonw.exe"
script = root & "\scripts\dev_servers.py"
If Not files.FileExists(python) Then
    MsgBox "Python environment not found.", vbCritical, "SWASTYA"
    WScript.Quit 1
End If
If Not files.FileExists(script) Then
    MsgBox "Launcher missing: scripts\dev_servers.py", vbCritical, "SWASTYA"
    WScript.Quit 1
End If
shell.Run Chr(34) & python & Chr(34) & " " & Chr(34) & script & Chr(34) & " stop", 0, False
