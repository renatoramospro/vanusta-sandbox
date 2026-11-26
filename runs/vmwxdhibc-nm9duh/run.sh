#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwxdhibc-nm9duh====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwxdhibc-nm9duh exit=${code}====="
exit "$code"
