#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmx090u0y-8chmx6====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmx090u0y-8chmx6 exit=${code}====="
exit "$code"
