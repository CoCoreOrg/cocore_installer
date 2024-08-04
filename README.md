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

Then, open `cocore_installer/task_worker.py` and find the line that says

```bash
WEBSOCKET_SERVER = "ws://192.168.3.11:3001/vm"
```

Change the IP address on this line to the IP of the host server.

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

When you are finished with the VM, run `reboot` to shut it down.
