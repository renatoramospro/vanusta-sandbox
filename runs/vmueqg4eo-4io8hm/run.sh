#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmueqg4eo-4io8hm====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmueqg4eo-4io8hm exit=${code}====="
exit "$code"
