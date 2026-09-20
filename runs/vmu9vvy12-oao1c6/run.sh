#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmu9vvy12-oao1c6====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmu9vvy12-oao1c6 exit=${code}====="
exit "$code"
