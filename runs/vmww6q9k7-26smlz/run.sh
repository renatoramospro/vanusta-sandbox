#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmww6q9k7-26smlz====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmww6q9k7-26smlz exit=${code}====="
exit "$code"
