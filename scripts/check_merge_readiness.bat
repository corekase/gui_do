@echo off
setlocal
python "%~dp0check_merge_readiness.py" %*
if errorlevel 1 (
  echo check_merge_readiness reported issues. Review the output above.
  exit /b 1
)
echo check_merge_readiness completed.
