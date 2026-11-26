#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwwzk83p-26gfow====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwwzk83p-26gfow exit=${code}====="
exit "$code"
