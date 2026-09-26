#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuidu4di-3wjt29====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuidu4di-3wjt29 exit=${code}====="
exit "$code"
