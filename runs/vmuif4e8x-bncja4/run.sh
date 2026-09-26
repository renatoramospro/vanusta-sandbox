#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuif4e8x-bncja4====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuif4e8x-bncja4 exit=${code}====="
exit "$code"
