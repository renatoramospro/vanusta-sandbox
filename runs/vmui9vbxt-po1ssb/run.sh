#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmui9vbxt-po1ssb====="
(
  set -e
  python 'wal_engine_v2.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmui9vbxt-po1ssb exit=${code}====="
exit "$code"
