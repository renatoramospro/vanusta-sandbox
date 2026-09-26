#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmui60jvt-6stuxs====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmui60jvt-6stuxs exit=${code}====="
exit "$code"
