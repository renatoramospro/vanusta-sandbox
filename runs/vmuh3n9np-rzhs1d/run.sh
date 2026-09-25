#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuh3n9np-rzhs1d====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuh3n9np-rzhs1d exit=${code}====="
exit "$code"
