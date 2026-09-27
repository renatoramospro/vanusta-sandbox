#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmujb5vzr-oh57tq====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmujb5vzr-oh57tq exit=${code}====="
exit "$code"
