#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmul2toa5-f0q8jy====="
(
  set -e
  python 'database_migration_secure_concurrent.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmul2toa5-f0q8jy exit=${code}====="
exit "$code"
