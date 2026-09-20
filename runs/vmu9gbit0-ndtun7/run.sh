#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmu9gbit0-ndtun7====="
(
  set -e
  python 'binary_search_demo.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmu9gbit0-ndtun7 exit=${code}====="
exit "$code"
