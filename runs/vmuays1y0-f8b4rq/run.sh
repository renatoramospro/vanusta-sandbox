#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuays1y0-f8b4rq====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuays1y0-f8b4rq exit=${code}====="
exit "$code"
