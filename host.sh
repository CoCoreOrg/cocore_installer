#!/bin/bash

echo 'CoCore Host'

# Default values for CPUs and memory (optional if not provided)
CPUS=1
MEMORY=512

# Parse command line arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --cpus) CPUS="$2"; shift ;;
        --memory) MEMORY="$2"; shift ;;
        *) echo "Unknown parameter passed: $1"; exit 1 ;;
    esac
    shift
done

# Activate virtual environment and install the package
source venv/bin/activate
pip install .

# Pass the CPU and memory values to cocore-start-vm command
cocore-start-vm 1 --cpus "$CPUS" --memory "$MEMORY"
