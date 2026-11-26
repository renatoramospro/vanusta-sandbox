#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwxbk35p-ewywon====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwxbk35p-ewywon exit=${code}====="
exit "$code"
