#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmu9kxi1c-pjztay====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmu9kxi1c-pjztay exit=${code}====="
exit "$code"
