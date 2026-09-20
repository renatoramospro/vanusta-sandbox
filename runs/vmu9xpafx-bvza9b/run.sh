#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmu9xpafx-bvza9b====="
(
  set -e
  python 'contract_engine.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmu9xpafx-bvza9b exit=${code}====="
exit "$code"
