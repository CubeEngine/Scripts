@echo off
set "PHP=\xampp\php\php.exe"

set "PROJECTS_HOME=\Development\Minecraft"
set "CE_HOME=%PROJECTS_HOME%\CubeEngineDev\CubeEngine"

"%PHP%" start.php "%~1"
