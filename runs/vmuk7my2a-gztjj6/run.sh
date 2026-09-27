#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuk7my2a-gztjj6====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuk7my2a-gztjj6 exit=${code}====="
exit "$code"
