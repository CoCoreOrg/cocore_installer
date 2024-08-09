#!/bin/bash

set -e

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)
pushd "${SCRIPT_DIR}"

python3 -m venv venv
source venv/bin/activate
pip install .
cocore-install

popd

