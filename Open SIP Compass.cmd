@echo off
rem Opens SIP Compass at http://localhost:8765 so the Ask AI tab can reach Ollama.
rem A small window stays minimised while you use it; close it to stop. Nothing is reachable from other computers.
start "SIP Compass (close to stop)" /min powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0launcher\serve.ps1"
