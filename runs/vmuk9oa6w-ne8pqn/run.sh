#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuk9oa6w-ne8pqn====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuk9oa6w-ne8pqn exit=${code}====="
exit "$code"
