Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
WshShell.CurrentDirectory = scriptDir
bat = fso.BuildPath(scriptDir, "start_stt.bat")
cmd = "cmd.exe /c """ & bat & """"
WshShell.Run cmd, 0, False
