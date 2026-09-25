#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuhjiae3-wjb4q1====="
(
  set -e
  python 'json_parser.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuhjiae3-wjb4q1 exit=${code}====="
exit "$code"
