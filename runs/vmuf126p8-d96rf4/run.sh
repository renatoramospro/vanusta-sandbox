#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuf126p8-d96rf4====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuf126p8-d96rf4 exit=${code}====="
exit "$code"
