#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuj43dsl-ly7fl3====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuj43dsl-ly7fl3 exit=${code}====="
exit "$code"
