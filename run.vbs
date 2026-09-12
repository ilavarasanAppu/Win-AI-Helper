Set WshShell = CreateObject("WScript.Shell")
Set FSO = CreateObject("Scripting.FileSystemObject")

scriptDir = FSO.GetParentFolderName(WScript.ScriptFullName)

' Get the path to start.bat (same directory as this VBS file)
startBat = scriptDir & "\start.bat"

' Run start.bat hidden - it will install deps and launch app in background
WshShell.Run "cmd.exe /c " & Chr(34) & startBat & Chr(34), 0, False

WScript.Quit