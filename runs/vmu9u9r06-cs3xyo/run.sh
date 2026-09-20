#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmu9u9r06-cs3xyo====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmu9u9r06-cs3xyo exit=${code}====="
exit "$code"
