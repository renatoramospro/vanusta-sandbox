#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmufc7dpl-j0mu3v====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmufc7dpl-j0mu3v exit=${code}====="
exit "$code"
