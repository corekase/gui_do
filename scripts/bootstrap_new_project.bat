@echo off
setlocal
python "%~dp0bootstrap_new_project.py" new --scaffold --verify
if errorlevel 1 (
  echo bootstrap_new_project failed.
  exit /b 1
)
echo bootstrap_new_project completed.
