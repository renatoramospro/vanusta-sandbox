#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwxpa30q-erlshk====="
(
  set -e
  python 'simulation.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwxpa30q-erlshk exit=${code}====="
exit "$code"
