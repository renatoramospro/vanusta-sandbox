#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmui7xz4p-heow39====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmui7xz4p-heow39 exit=${code}====="
exit "$code"
