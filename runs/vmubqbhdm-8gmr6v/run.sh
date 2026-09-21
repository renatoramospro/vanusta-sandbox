#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmubqbhdm-8gmr6v====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmubqbhdm-8gmr6v exit=${code}====="
exit "$code"
