#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmufcqmg1-jdi2tt====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest 'PyJWT==2.8.0' 'pytest==8.0.0' 'coverage==7.4.1'
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmufcqmg1-jdi2tt exit=${code}====="
exit "$code"
