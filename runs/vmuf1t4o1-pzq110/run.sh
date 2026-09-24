#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuf1t4o1-pzq110====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuf1t4o1-pzq110 exit=${code}====="
exit "$code"
