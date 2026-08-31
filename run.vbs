' ⚡ Win AI Helper — Native Silent Launcher (Zero Terminal Window)
Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)

pythonwExe = WshShell.ExpandEnvironmentStrings("%USERPROFILE%") & "\AppData\Local\hermes\hermes-agent\venv\Scripts\pythonw.exe"
If Not fso.FileExists(pythonwExe) Then
    pythonwExe = "pythonw.exe"
End If

WshShell.CurrentDirectory = scriptDir
WshShell.Run """" & pythonwExe & """ """ & scriptDir & "\main.py""", 0, False
