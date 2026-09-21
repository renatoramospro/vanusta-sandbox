#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuaum5wx-49yls6====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuaum5wx-49yls6 exit=${code}====="
exit "$code"
