#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwwrmf5l-sdvgg6====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwwrmf5l-sdvgg6 exit=${code}====="
exit "$code"
