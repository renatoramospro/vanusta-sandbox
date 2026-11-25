#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwwrat5a-5dqn66====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwwrat5a-5dqn66 exit=${code}====="
exit "$code"
