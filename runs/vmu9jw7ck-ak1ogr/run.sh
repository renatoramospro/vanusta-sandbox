#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmu9jw7ck-ak1ogr====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmu9jw7ck-ak1ogr exit=${code}====="
exit "$code"
