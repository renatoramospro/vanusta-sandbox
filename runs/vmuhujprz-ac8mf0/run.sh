#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuhujprz-ac8mf0====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuhujprz-ac8mf0 exit=${code}====="
exit "$code"
