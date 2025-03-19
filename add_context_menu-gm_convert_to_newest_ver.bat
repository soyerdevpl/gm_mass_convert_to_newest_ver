@echo off
SET "PYTHON_PATH=C:\Python310\python.exe"
SET "SCRIPT_PATH=D:\Projects\_ai\_nogm_python_itd\_konwersja gm\gm_convert_to_newest_ver.py"

REM Add context menu
reg add "HKEY_CLASSES_ROOT\*\shell\gm_convert_to_newest_ver" /v "MUIVerb" /t REG_SZ /d "gm_convert_to_newest_ver" /f
reg add "HKEY_CLASSES_ROOT\*\shell\gm_convert_to_newest_ver\command" /t REG_SZ /d "\"%PYTHON_PATH%\" \"%SCRIPT_PATH%\" \"%%1\"" /f

echo "Context menu option added successfully."
pause