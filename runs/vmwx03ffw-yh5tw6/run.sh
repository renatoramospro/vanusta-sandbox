#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwx03ffw-yh5tw6====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwx03ffw-yh5tw6 exit=${code}====="
exit "$code"
