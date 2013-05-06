@echo off

echo REMOVING BUILD DIRECTORY

rmdir /s /q build
rmdir /s /q palabre-src


mkdir palabre-src
mkdir palabre-src\etc

copy etc\palabre.conf palabre-src\etc

mkdir palabre-src\doc

copy doc\README.txt palabre-src\doc

mkdir palabre-src\palabre

copy palabre\*.py palabre-src\palabre

mkdir palabre-src\modules

copy modules\*.py palabre-src\modules

mkdir palabre-src\scripts

copy scripts\palabre palabre-src\scripts


copy Palabre.py palabre-src\
copy setup.py palabre-src\

copy AUTHORS palabre-src\
copy COPYING palabre-src\
copy MANIFEST palabre-src\
copy MANIFEST.IN palabre-src\
copy palabre.ico palabre-src\
copy README palabre-src\
copy PKG-INFO palabre-src\




pause