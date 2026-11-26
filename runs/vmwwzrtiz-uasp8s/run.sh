#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwwzrtiz-uasp8s====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwwzrtiz-uasp8s exit=${code}====="
exit "$code"
