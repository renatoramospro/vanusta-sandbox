#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmug0nap3-sjynf6====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmug0nap3-sjynf6 exit=${code}====="
exit "$code"
