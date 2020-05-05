# less-Windows
GNU less compiled for Windows 10

A 32-bit Windows 10 binary for `less.exe` and `less.key` is provided on the [Releases Page](https://github.com/jftuga/less-Windows/releases).

___

## How to Compile **less** from source

___

## Installing the Docker Image

1) Follow these instructions: [Install Build Tools into a container](https://docs.microsoft.com/en-us/visualstudio/install/build-tools-container?view=vs-2019)
* * Their `Dockerfile` needs a small modification to include the [Visual Studio Build Tools](https://devblogs.microsoft.com/cppblog/using-msvc-in-a-docker-container-for-your-c-projects/).  This allows for C / C++ development.  It specifically adds `cl.exe` *(the C compiler)*, `link.exe` and `nmake.exe` which are required to build `less`.

2) Here is the needed change, which is already included in my  [Dockerfile](https://github.com/jftuga/less-Windows/blob/master/Dockerfile).

```sh
--add Microsoft.VisualStudio.Workload.VCTools --includeRecommended `
```

3) **Note:** Their `docker build` command can take several minutes to complete!

## Source Code Changes

1) Download the newest version of: [less - a clean-compiling, more Windows-friendly, fork of the original version](https://github.com/rivy/less) 
* *  A zip package is provided on his [Release Page](https://github.com/rivy/less/releases).  At the time of this writing, this is **less 557**.

2) The downloaded file may be called either `less-557.zip` or `v557.zip`

3) Unzip the source to `c:\`

```bat
unzip -d c:\ less-557.zip
```

4) You will also need to manually modify `charset.c`.

* * Add this line of code  just before  `extern int bs_mode;` *(around line #32)*:

```c
#define WC_NO_BEST_FIT_CHARS 0x00000400
```

5) I have already provided this modification: [charset.c for less version 557](https://github.com/jftuga/less-Windows/blob/master/charset.c).

## Compilation

1) Start your docker container:

```bat
cd c:\BuildTools
docker run -i -t --rm --mount type=bind,src=c:\less,dst=c:\less buildtools2019
```

2) To compile `less.exe` and `lesskey.exe` run this command:

```bat
rem note: these commands are running from within your container
cd c:\less
nmake /f Makefile.win.msvc.nmake
```

3) You should now have version of `less.exe` that is about 33 KB and `lesskey.exe` that is about 119 KB in size.

4) You can now `exit` the Docker container

## Example binaries
```
C:\less>dir *.exe

Directory of C:\less

05/05/2020  08:51 AM           273,408 less.exe
05/05/2020  08:51 AM           121,856 lesskey.exe
               2 File(s)        395,264 bytes
```
