#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwxeztea-4zjg57====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwxeztea-4zjg57 exit=${code}====="
exit "$code"
