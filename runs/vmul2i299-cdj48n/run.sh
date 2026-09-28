#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmul2i299-cdj48n====="
(
  set -e
  python 'database_migration_concurrent.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmul2i299-cdj48n exit=${code}====="
exit "$code"
