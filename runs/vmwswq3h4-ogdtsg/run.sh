#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwswq3h4-ogdtsg====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwswq3h4-ogdtsg exit=${code}====="
exit "$code"
