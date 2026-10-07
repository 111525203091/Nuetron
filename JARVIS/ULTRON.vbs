Set WshShell = CreateObject("WScript.Shell")
strCurrentDirectory = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
WshShell.CurrentDirectory = strCurrentDirectory
WshShell.Run "pythonw app_launcher.py", 0, False
