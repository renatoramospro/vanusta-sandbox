#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvs1o6qn-4n8z62====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvs1o6qn-4n8z62 exit=${code}====="
exit "$code"
