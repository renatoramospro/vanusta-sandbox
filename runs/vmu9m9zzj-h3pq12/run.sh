#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmu9m9zzj-h3pq12====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmu9m9zzj-h3pq12 exit=${code}====="
exit "$code"
