@echo off

@REM start "Node server " cmd /k "node \"D:/.vscode/Vs programmes/Df Detector/server-side/server.js\""

echo ">> Node and Python backend start on..."

start "Node server " cmd /k "cd C:/Users/SOUHARDYA/OneDrive/Desktop/DFD/WEB & node server.js"
start "Python server " cmd /k "cd C:/Users/SOUHARDYA/OneDrive/Desktop/DFD/API & uvicorn main:app --reload"
pause

echo ">> Terminate from bash work"