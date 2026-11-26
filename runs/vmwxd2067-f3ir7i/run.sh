#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwxd2067-f3ir7i====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwxd2067-f3ir7i exit=${code}====="
exit "$code"
