#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmul1nabm-77xv2m====="
(
  set -e
  python 'database_migration_simulation.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmul1nabm-77xv2m exit=${code}====="
exit "$code"
