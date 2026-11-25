#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmww6y1pg-b3tf4s====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmww6y1pg-b3tf4s exit=${code}====="
exit "$code"
