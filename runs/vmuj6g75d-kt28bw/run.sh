#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuj6g75d-kt28bw====="
(
  set -e
  python 'skiplist_concorrente.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuj6g75d-kt28bw exit=${code}====="
exit "$code"
