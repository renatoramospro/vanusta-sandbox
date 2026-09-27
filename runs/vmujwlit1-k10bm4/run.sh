#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmujwlit1-k10bm4====="
(
  set -e
  python 'vector_search.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmujwlit1-k10bm4 exit=${code}====="
exit "$code"
