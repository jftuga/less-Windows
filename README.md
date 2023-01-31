# less-Windows [![nightly](https://github.com/jftuga/less-Windows/actions/workflows/nightly.yml/badge.svg)](https://github.com/jftuga/less-Windows/actions/workflows/nightly.yml)

GNU [less](https://en.wikipedia.org/wiki/Less_\(Unix\)) compiled for Windows from the [less source](http://greenwoodsoftware.com/less/) via GitHub Actions. New versions are being checked daily, and builds are compiled with the latest version of Visual Studio.

## Installation

Binaries for `less.exe` (and `lesskey.exe`) are provided on the [Releases Page](https://github.com/jftuga/less-Windows/releases). Download the appropriate one for your system. If you prefer to install less via a package manager, you can choose one of the following options:

### Winget

A new version is pushed to the upstream [winget-pkgs](https://github.com/microsoft/winget-pkgs) for every release:

```powershell
winget install jftuga.less
```

### Chocolatey

[less](https://community.chocolatey.org/packages/less) is available in the Community Repository:
```powershell
choco install less
```

### Scoop

[less](https://scoop.sh/#/apps?q=main%2Fless&s=0&d=1&o=true) is available in the Main bucket:
```powershell
scoop install less
```
