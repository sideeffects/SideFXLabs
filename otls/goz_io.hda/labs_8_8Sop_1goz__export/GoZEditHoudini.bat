@echo off
for /f "delims== tokens=1,2" %%G in (GoZ_Config.txt) do set H_PATH=%%H 

set "H_PATH=%H_PATH:/=\%"
echo %H_PATH%

For %%A in (%H_PATH%) do (
    echo full path: %%~dA%%~pA
    set hython=%%~dA%%~pAhython.exe
    )
    
call "%hython%" GoZBrushToHoudini.py