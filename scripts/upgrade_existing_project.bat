@echo off
setlocal
python "%~dp0bootstrap_new_project.py" upgrade --verify
if errorlevel 1 (
  echo upgrade_existing_project failed.
  exit /b 1
)
echo upgrade_existing_project completed.
