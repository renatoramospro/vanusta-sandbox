#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuduu1in-8o8wih====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuduu1in-8o8wih exit=${code}====="
exit "$code"
