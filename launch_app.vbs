Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
ScriptDir = fso.GetParentFolderName(WScript.ScriptFullName)

' Run desktop_app.py using venv python without showing any console window (0 = hide window)
PythonExe = ScriptDir & "\venv\Scripts\python.exe"
ScriptPath = ScriptDir & "\desktop_app.py"

WshShell.CurrentDirectory = ScriptDir
WshShell.Run """" & PythonExe & """ """ & ScriptPath & """", 0, False
