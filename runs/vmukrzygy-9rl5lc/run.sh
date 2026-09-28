#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmukrzygy-9rl5lc====="
(
  set -e
  python 'experiment.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmukrzygy-9rl5lc exit=${code}====="
exit "$code"
