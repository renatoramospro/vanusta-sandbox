#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwx1dmvu-c24437====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwx1dmvu-c24437 exit=${code}====="
exit "$code"
