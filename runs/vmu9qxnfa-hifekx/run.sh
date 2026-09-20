#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmu9qxnfa-hifekx====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmu9qxnfa-hifekx exit=${code}====="
exit "$code"
