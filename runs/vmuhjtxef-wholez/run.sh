#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuhjtxef-wholez====="
(
  set -e
  python 'json_parser.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuhjtxef-wholez exit=${code}====="
exit "$code"
