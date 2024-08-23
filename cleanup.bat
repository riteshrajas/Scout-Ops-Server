@echo off

REM Specify the paths to clean up
set "build_dir=.\build"
set "spec_file=.\server.spec"

REM Check if the build directory exists, and if so, delete it
if exist "%build_dir%" (
    echo Deleting build directory...
    rmdir /s /q "%build_dir%"
)

REM Check if the dist directory exists, and if so, delete it


REM Check if the .spec file exists, and if so, delete it
if exist "%spec_file%" (
    echo Deleting spec file...
    del /f "%spec_file%"
)

REM Optionally, remove the __pycache__ directories if they exist
for /d /r . %%d in (__pycache__) do (
    if exist "%%d" (
        echo Deleting __pycache__ directory %%d...
        rmdir /s /q "%%d"
    )
)

echo Cleanup complete.

pause
