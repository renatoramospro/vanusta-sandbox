#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmubra50w-qxq43v====="
(
  set -e
  python -m pip install -q --disable-pip-version-check 'PyJWT==2.8.0' 'cryptography==41.0.3'
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmubra50w-qxq43v exit=${code}====="
exit "$code"
