#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmu9uymbm-ttkfcw====="
(
  set -e
  python 'container.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmu9uymbm-ttkfcw exit=${code}====="
exit "$code"
