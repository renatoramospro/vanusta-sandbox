#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuiaas1b-oi3ezq====="
(
  set -e
  python 'wal_engine_v3.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuiaas1b-oi3ezq exit=${code}====="
exit "$code"
