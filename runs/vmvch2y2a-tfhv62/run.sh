#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvch2y2a-tfhv62====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvch2y2a-tfhv62 exit=${code}====="
exit "$code"
