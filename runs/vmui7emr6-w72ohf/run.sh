#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmui7emr6-w72ohf====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmui7emr6-w72ohf exit=${code}====="
exit "$code"
