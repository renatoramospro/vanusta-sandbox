#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwxhvq3d-37f15v====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwxhvq3d-37f15v exit=${code}====="
exit "$code"
