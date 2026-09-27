#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuj4qh0n-c01ubh====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuj4qh0n-c01ubh exit=${code}====="
exit "$code"
