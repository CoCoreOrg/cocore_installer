# CoCore

This document summarizes the proof-of-concept CoCore implementation.

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
