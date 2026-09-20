#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmu9qabmg-o2by74====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmu9qabmg-o2by74 exit=${code}====="
exit "$code"
