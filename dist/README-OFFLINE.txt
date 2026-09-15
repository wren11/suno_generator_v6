Scansion — offline kit

Unzip, then double-click start.bat (Windows) or run ./start.sh (Mac/Linux).
A browser tab opens the studio. Keep the black studio window open.

Need once
- Node.js 20+ LTS  https://nodejs.org
- Python 3.11 or 3.12, 64-bit, with "Add python.exe to PATH"
  https://www.python.org/downloads/

First Generate needs PyTorch + Transformers in that Python. start.bat
installs the CPU wheels from the official PyTorch index (internet once).
After that, writing sheets is local. Paste into Suno when you want audio.

If a browser says Not Found, the studio window did not start. Install Node,
run start.bat again, and wait for "Listening on" in that window.

Layout
- server/     studio
- foundry/    Scansion-LM weights + Python sidecar
- start.bat   Windows launcher
- start.sh    Mac / Linux launcher
