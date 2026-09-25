#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuhgq057-klzk8e====="
(
  set -e
  python 'regex_engine.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuhgq057-klzk8e exit=${code}====="
exit "$code"
