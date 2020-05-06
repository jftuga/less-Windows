# less-Windows
GNU [less](https://en.wikipedia.org/wiki/Less_\(Unix\)) compiled for Windows 10

# May 6, 2020 - I have discovered that colors do not work correctly in this version, use the Master branch instead.

32-bit Windows 10 binaries for `less.exe` and `lesskey.key` are provided on the [Releases Page](https://github.com/jftuga/less-Windows/releases).

___

## How to Compile **less** from source

___

## Installing the Docker Image

1) Follow these instructions: [Install Build Tools into a container](https://docs.microsoft.com/en-us/visualstudio/install/build-tools-container?view=vs-2019)
* * Their `Dockerfile` needs a small modification to include the [Visual Studio Build Tools](https://devblogs.microsoft.com/cppblog/using-msvc-in-a-docker-container-for-your-c-projects/).  This allows for C / C++ development.  It specifically adds `cl.exe` *(the C compiler)*, `link.exe` and `nmake.exe` which are required to build `less`.

2) Here is the needed change, which is already included in my  [Dockerfile](https://github.com/jftuga/less-Windows/blob/master/Dockerfile).

```bat
--add Microsoft.VisualStudio.Workload.VCTools --includeRecommended `
```
* *  I also removed `AzureBuildTools` as it is unnecessary.

3) As per their instructions, build the image:

```bat
docker build -t buildtools2019:latest -m 2GB .
```

4) **Note:** This `docker build` command can take several minutes to complete as it is a **14 GB** image.

## Source Code Changes

1) Download the newest version of: [less - a clean-compiling, more Windows-friendly, fork of the original version](https://github.com/rivy/less) 
* *  A zip package is provided on his [Release Page](https://github.com/rivy/less/releases).  At the time of this writing, this is **less 557**.

2) The downloaded file may be called either `less-557.zip` or `v557.zip`

3) Unzip the source to `c:\`

```bat
unzip -d c:\ less-557.zip
cd c:\
rem renaming will make it easier to compile future versions with the other commands given below
ren less-557 less
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
cd c:\
docker run -i -t --rm --mount type=bind,src=c:\less,dst=c:\less buildtools2019
```

2) To compile `less.exe` and `lesskey.exe` run this command:

```bat
rem note: these commands are running from within your container
cd c:\less
nmake /f Makefile.win.msvc.nmake
```

3) You should now have version of `less.exe` that is about 267 KB in size and a `lesskey.exe` that is about 119 KB in size.

4) You can now `exit` the Docker container

## Example binaries
```
PS C:\less> dir *.exe
    Directory: C:\less
Mode                LastWriteTime         Length Name
----                -------------         ------ ----
-a----         5/5/2020   9:57 AM         273408 less.exe
-a----         5/5/2020   9:57 AM         121856 lesskey.exe
```

## Clean Up
1) Once you have exited the container, you can now remove the Docker image, which will look something like this, but with different ID numbers:

```
C:\>docker image rm buildtools2019:latest
Untagged: buildtools2019:latest
Deleted: sha256:61907e0a943cf4fcb75f32e27f8d8e64e41ee3a0543a1a76da481802ce2e54c6
Deleted: sha256:7f8448ecb8c4d88ba0bfdb17b68c93c36b02581d1ef4b3531cf58e36227f902e
Deleted: sha256:d98bf876297aea21966613ba9a1185b655bbcf34739b8196fea6f176897a1940
Deleted: sha256:96e20ee1eac6e6d02b32d646b52f8ed14720819f104eff06ce6aef34b979f96b
Deleted: sha256:affaa7cc226aff9c3ae355f72f85570db2e44e6812e298cab18c5533bbae39b1
Deleted: sha256:76af3aa750bb9b86c95d2218363b08e1074e3768ab25358734a31ef1df6b2efa
Deleted: sha256:29ea33c2680dedaaf4b2a1e294f86b95482e7f28f42ef2ea0ae76b615049045e
Deleted: sha256:9860872f53fc9f82389efe6b22b1a9e3cdc23b09da3892595ae49fbdf2463563
```

2) Remove the unneeded `BuildTools` folder

```
c:\>rd /s/q BuildTools
```

3) Your `less.exe` and `lesskey.exe` binaries should still be in your `C:\less` folder.
