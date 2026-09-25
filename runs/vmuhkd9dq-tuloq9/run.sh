#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuhkd9dq-tuloq9====="
(
  set -e
  python 'json_parser.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuhkd9dq-tuloq9 exit=${code}====="
exit "$code"
