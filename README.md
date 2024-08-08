# CoCore

This document summarizes the proof-of-concept CoCore implementation.

## Build and Install

To build and install the app, run the following commands in the `cocore_installer` root directory:

```bash
python3 -m venv venv
source venv/bin/activate
pip install .
cocore-install
```


## Uninstallation Instructions

To completely remove CoCore and all its components from your system, run the following uninstall script. This will delete all dependencies, uninstall Firecracker, remove any disk data and mounted images created during the installation, and reset the machine to its pre-installation state.

```bash
bash cocore_installer/uninstall.sh
```

This will:

* Terminate any running Firecracker processes,
* Remove Firecracker binaries and related files,
* Unmount and delete disk images,
* Remove installed Python packages and the virtual environment,
* Delete configuration files, authentication keys, and tokens,
* Revert any network configuration changes,
* Remove temporary and log files generated during the installation and operation of CoCore.

After running the uninstaller, your system will be reset to its state prior to CoCore installation.
