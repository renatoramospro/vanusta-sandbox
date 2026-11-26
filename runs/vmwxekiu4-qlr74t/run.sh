#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwxekiu4-qlr74t====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwxekiu4-qlr74t exit=${code}====="
exit "$code"
