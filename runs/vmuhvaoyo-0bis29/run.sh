#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuhvaoyo-0bis29====="
(
  set -e
  python -m pip install -q --disable-pip-version-check pytest
  python -m pytest -q
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuhvaoyo-0bis29 exit=${code}====="
exit "$code"
