#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuhksmzm-72d1xz====="
(
  set -e
  python 'json_parser.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuhksmzm-72d1xz exit=${code}====="
exit "$code"
