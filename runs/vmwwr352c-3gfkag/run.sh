#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwwr352c-3gfkag====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwwr352c-3gfkag exit=${code}====="
exit "$code"
