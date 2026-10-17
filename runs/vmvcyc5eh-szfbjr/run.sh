#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvcyc5eh-szfbjr====="
(
  set -e
  python -m pip install -q --disable-pip-version-check 'psutil>=5.9.0'
  python 'monitor.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvcyc5eh-szfbjr exit=${code}====="
exit "$code"
