@echo off

echo REMOVING BUILD DIRECTORY

rmdir /s /q build
rmdir /s /q dist
rmdir /s /q palabre-windows

c:\python25\python.exe setup_windows.py py2exe 

rmdir /s /q build

ren dist palabre-windows

pause