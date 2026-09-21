#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuapcehm-0c9458====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuapcehm-0c9458 exit=${code}====="
exit "$code"
