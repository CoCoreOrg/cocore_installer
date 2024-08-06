# CoCore

This document summarizes the proof-of-concept CoCore implementation.

## Setup Networking

Before you can run the app, you will need to set up networking on the host machine. First, open `cocore_installer/setup_network.sh` and find the line that says

```
HOST_IFACE=elo1
```

Change this line to your host network interface (e.g. `eth1`), then run:

```bash
bash cocore_installer/setup_network.sh
```

## Build and Install

To build and install the app, run the following commands in the `cocore_installer` root directory:

```bash
python3 -m venv venv
source venv/bin/activate
pip install .
cocore-install
```

Enter an authentication code when prompted. You will need two terminals to run the proof-of-concept: one to run the task server and one to run the VM. In the first, run:

```bash
source venv/bin/activate
cocore-task-server
```

The task server will boot and say it is ready to accept connections.

In the second, run:

```bash
source venv/bin/activate
cocore-setup-firecracker
```

The VM will start up and you will get a command prompt. A task handler also starts up with the VM -- to see the task handler output, you can run:

```bash
journalctl -u cocore -f
```

Press Ctrl + D to exit the output view.

To test running commands with the control server, navigate to the address of the **host server** in your web browser. For example, my host server address is `192.168.3.11` and the web server runs on port `3001`, so I can navigate my web browser to `http://192.168.3.11:3001`.

When you are finished with the VM, run `reboot` to shut it down.


## Uninstallation Instructions

To completely remove CoCore and all its components from your system, run the following uninstall script. This will delete all dependencies, uninstall Firecracker, remove any disk data and mounted images created during the installation, and reset the machine to its pre-installation state.

```bash
bash cocore_installer/uninstall_cocore.sh
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