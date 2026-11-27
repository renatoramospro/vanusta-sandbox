#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwyjt7je-arwvmr====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwyjt7je-arwvmr exit=${code}====="
exit "$code"
