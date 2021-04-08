Set WshShell = CreateObject ("WScript.shell")
Dim strArgs
strArgs = "cmd /c + bat/크로디버깅모드(64비트).bat"
WshShell.Run strArgs, 0, false
