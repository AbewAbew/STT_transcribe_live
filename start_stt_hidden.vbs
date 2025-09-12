' Modern Global STT Hidden Launcher v2.0
' Starts the Modern Global STT system silently in background

Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

' Get script directory
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
WshShell.CurrentDirectory = scriptDir

' Check if virtual environment exists and build command
If fso.FolderExists(fso.BuildPath(scriptDir, "venv\Scripts")) Then
    ' Use virtual environment
    pythonPath = fso.BuildPath(scriptDir, "venv\Scripts\python.exe")
    If fso.FileExists(pythonPath) Then
        cmd = """" & pythonPath & """ modern_global_stt.py"
    Else
        cmd = "python modern_global_stt.py"
    End If
Else
    cmd = "python modern_global_stt.py"
End If

' Run the Modern Global STT system hidden (window style 0 = hidden)
WshShell.Run cmd, 0, False
