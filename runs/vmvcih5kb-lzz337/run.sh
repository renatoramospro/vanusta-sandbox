#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvcih5kb-lzz337====="
(
  set -e
  python 'jemalloc_robust_sim.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvcih5kb-lzz337 exit=${code}====="
exit "$code"
