#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvd4rnal-elyjaq====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvd4rnal-elyjaq exit=${code}====="
exit "$code"
