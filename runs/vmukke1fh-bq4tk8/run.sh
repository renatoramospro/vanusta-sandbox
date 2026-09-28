#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmukke1fh-bq4tk8====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmukke1fh-bq4tk8 exit=${code}====="
exit "$code"
