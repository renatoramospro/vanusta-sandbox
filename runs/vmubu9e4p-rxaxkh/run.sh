#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmubu9e4p-rxaxkh====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmubu9e4p-rxaxkh exit=${code}====="
exit "$code"
