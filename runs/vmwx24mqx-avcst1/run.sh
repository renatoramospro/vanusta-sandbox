#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwx24mqx-avcst1====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwx24mqx-avcst1 exit=${code}====="
exit "$code"
