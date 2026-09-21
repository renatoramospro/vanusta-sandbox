#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuap4ofw-x981vb====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuap4ofw-x981vb exit=${code}====="
exit "$code"
