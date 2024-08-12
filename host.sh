#!/bin/bash

echo 'CoCore Host'

source venv/bin/activate
pip install .
cocore-start-vm
