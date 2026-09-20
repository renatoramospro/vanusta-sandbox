#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmu9fdbqx-8gyg6y====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmu9fdbqx-8gyg6y exit=${code}====="
exit "$code"
