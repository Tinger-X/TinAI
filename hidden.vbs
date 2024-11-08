Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "python main.py config.json", 0, True
Set WshShell = Nothing
