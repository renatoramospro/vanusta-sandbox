#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwyk8k5w-e8fxvq====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwyk8k5w-e8fxvq exit=${code}====="
exit "$code"
