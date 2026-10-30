#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvuwrl9b-zpabbk====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvuwrl9b-zpabbk exit=${code}====="
exit "$code"
