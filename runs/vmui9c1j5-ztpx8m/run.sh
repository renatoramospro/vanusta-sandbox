#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmui9c1j5-ztpx8m====="
(
  set -e
  python 'wal_engine.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmui9c1j5-ztpx8m exit=${code}====="
exit "$code"
