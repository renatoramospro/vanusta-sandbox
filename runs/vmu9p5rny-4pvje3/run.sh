#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmu9p5rny-4pvje3====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmu9p5rny-4pvje3 exit=${code}====="
exit "$code"
