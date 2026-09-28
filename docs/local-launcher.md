# Start without terminal windows (Windows)

Double-click `Start Badabee.vbs` in the repository root. It starts FastAPI and Vite with hidden console windows, waits for both to respond, and opens http://localhost:5173/ in your default browser. No virtual-environment activation is needed.

Double-click `Stop Badabee.vbs` to stop servers created by this launcher. A process's executable and creation time are checked before its process tree is stopped. Servers already running in your own terminals are reused but are not stopped by this shortcut. For the first switch to hidden mode, stop both old terminal servers with Ctrl+C and then use Start Badabee.

Requirements: Windows Script Host, Node.js on PATH, the existing `backend/.venv` with dependencies installed, `swastya/node_modules`, a configured backend `.env`, and a running PostgreSQL service. The launcher does not start or stop PostgreSQL and does not modify account data.

Startup failures display a short error dialog. Logs are written to `.dev-runtime/backend.log`, `.dev-runtime/frontend.log`, and `.dev-runtime/launcher.log`. This local folder is ignored by Git. To keep the launchers convenient, create desktop shortcuts pointing to the VBS files; do not move the files out of the project.

Frontend changes, including the victim dashboard, refresh through Vite. After backend code, dependency or environment changes, use Stop Badabee and then Start Badabee. The original `start-dev.bat` remains available for debugging with visible terminals. These launchers are for local development, not a production hosting service.

All dashboards use the same frontend and backend; the signed-in account determines which dashboard appears. Closing the browser tab does not stop these servers. Double-click Stop Badabee when finished. No dedicated desktop window or desktop-window package is required.
