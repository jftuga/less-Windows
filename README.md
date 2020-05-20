# less-Windows
GNU [less](https://en.wikipedia.org/wiki/Less_\(Unix\)) compiled for Windows 10 from the [less source](http://greenwoodsoftware.com/less/).

A stand-alone 64-bit Windows 10 binary for `less.exe` is provided on the [Releases Page](https://github.com/jftuga/less-Windows/releases).

[AppVeyor build history](https://ci.appveyor.com/project/jftuga/less-windows/history) - A new build is attempted each day.  A successful build only occurs when a new version is built (upstream has been updated).  Otherwise, a failure is normally seen when there is not a new upstream version.  This version is compiled with `Visual Studio 2019`.

___

## **Optional**: How to Compile **less** from source with the **mingw-w64** compiler
___

## Installing mingw-w64 
1) [mingw-w64](http://mingw-w64.org/) is a port of the GCC compiler for Windows.
* * Download `mingw-w64-install.exe` from here: [Mingw-builds](http://mingw-w64.org/doku.php/download/mingw-builds).
2) Select these installer options:
* * Version: `8.1.0`
* * Architecture: `x86_64`
* * Threads: `posix`
* * Exception: `seh`
* * Build Revision: `0`
3) This will install about **440 MB** of files into `C:\Program Files\mingw-w64`

## Installing Perl - *the easy way*
1) `Perl` is required to build two source files: `funcs.h` and `help.c`
2) [Git for Windows](https://git-scm.com/download/win) already includes Perl.
* * I am currently using `Git-2.26.2-64-bit.exe`

## Source Code
1) Clone the newest version of: [Less - text pager](https://github.com/gwsw/less) into the `c:\less` folder.

```bat
cd c:\
git clone https://github.com/gwsw/less.git
```

## Environment
1) Locate and run the `mingw-w64.bat` file to properly configure the PATH environment.
2) For the `x86_64 8.1.0 seh` version, it is located here:
* * `c:\Program Files\mingw-w64\x86_64-8.1.0-posix-seh-rt_v6-rev0\mingw-w64.bat`

## Compilation
1) To compile `less.exe` run these commands:

```bat
rem configure PATH for mingw-w64
"c:\Program Files\mingw-w64\x86_64-8.1.0-posix-seh-rt_v6-rev0\mingw-w64.bat"
rem configure PATH to also include Perl
set PATH=%PATH%;c:\Program Files\Git\usr\bin
rem ensure perl is working by display its version...
perl -v
rem compile the less source code into less.exe
cd c:\less
mingw32-make.exe -f Makefile.wng REGEX_PACKAGE=regcomp-local
```

2) After compilation completes, you should now have a version of `less.exe` that is about 255 KB in size. `lessecho.exe` and `lesskey.exe` should have also been compiled.

## Example binaries
```
 Directory of c:\less

05/06/2020  10:30 AM           260,711 less.exe
05/06/2020  10:30 AM            57,360 lessecho.exe
05/06/2020  10:30 AM            65,526 lesskey.exe
               3 File(s)        383,597 bytes
```

## Clean Up
1) Remove the `mingw-w64` compiler by using a `Run as administrator` command prompt:

```bat
"c:\Program Files\mingw-w64\x86_64-8.1.0-posix-seh-rt_v6-rev0\uninstall.exe"
rd /s/q "c:\Program Files\mingw-w64"
```
2) The `less.exe`, `lessecho.exe`, and `lesskey.exe` binaries should still exist in the `C:\less` folder.
