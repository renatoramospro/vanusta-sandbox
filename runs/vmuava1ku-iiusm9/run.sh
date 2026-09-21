#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuava1ku-iiusm9====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuava1ku-iiusm9 exit=${code}====="
exit "$code"
