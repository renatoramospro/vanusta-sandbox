#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmu9joip6-igyovv====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmu9joip6-igyovv exit=${code}====="
exit "$code"
