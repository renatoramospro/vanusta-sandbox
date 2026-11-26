#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwxoeqh8-toew4x====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwxoeqh8-toew4x exit=${code}====="
exit "$code"
