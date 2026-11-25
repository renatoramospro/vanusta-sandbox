#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwwgpbug-68claa====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwwgpbug-68claa exit=${code}====="
exit "$code"
