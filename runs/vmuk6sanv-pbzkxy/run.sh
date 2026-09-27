#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuk6sanv-pbzkxy====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuk6sanv-pbzkxy exit=${code}====="
exit "$code"
