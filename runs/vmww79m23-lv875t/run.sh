#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmww79m23-lv875t====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmww79m23-lv875t exit=${code}====="
exit "$code"
