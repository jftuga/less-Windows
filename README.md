# less-Windows [![nightly](https://github.com/jftuga/less-Windows/actions/workflows/nightly.yml/badge.svg)](https://github.com/jftuga/less-Windows/actions/workflows/nightly.yml)

GNU [less](https://en.wikipedia.org/wiki/Less_\(Unix\)) compiled for Windows 10 from the [less source](http://greenwoodsoftware.com/less/).

## Download

Binaries for `less.exe` (and `lesskey.exe`) are provided on the [Releases Page](https://github.com/jftuga/less-Windows/releases). Download the appropriate one for your system.

### [GitHub Actions](https://github.com/jftuga/less-Windows/actions)

The actions check for new versions 3 times a week. The `GitHub Actions` builds are compiled with the latest version of Visual Studio.

### Winget

A new version is pushed to the upstream [winget-pkgs](https://github.com/microsoft/winget-pkgs) for every release. To install less in Winget, run the following commands:

```powershell
winget install JohnTaylor.less
winget install JohnTaylor.lesskey # already installed in the JohnTaylor.less package if you have the dependencies feature enabled
```
