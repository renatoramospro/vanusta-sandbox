#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmx08hlh3-hs83rz====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmx08hlh3-hs83rz exit=${code}====="
exit "$code"
