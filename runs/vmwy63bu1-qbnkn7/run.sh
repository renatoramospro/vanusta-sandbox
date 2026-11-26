#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwy63bu1-qbnkn7====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwy63bu1-qbnkn7 exit=${code}====="
exit "$code"
