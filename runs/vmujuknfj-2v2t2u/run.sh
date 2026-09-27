#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmujuknfj-2v2t2u====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmujuknfj-2v2t2u exit=${code}====="
exit "$code"
