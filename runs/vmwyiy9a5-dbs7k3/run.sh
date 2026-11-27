#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwyiy9a5-dbs7k3====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwyiy9a5-dbs7k3 exit=${code}====="
exit "$code"
