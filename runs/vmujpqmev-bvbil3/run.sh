#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmujpqmev-bvbil3====="
(
  set -e
  python 'search_engine.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmujpqmev-bvbil3 exit=${code}====="
exit "$code"
