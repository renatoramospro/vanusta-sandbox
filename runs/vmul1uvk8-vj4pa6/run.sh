#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmul1uvk8-vj4pa6====="
(
  set -e
  python 'database_migration_simulation.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmul1uvk8-vj4pa6 exit=${code}====="
exit "$code"
