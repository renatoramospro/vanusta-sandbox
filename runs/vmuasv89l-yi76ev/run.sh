#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuasv89l-yi76ev====="
(
  set -e
  python 'replay_system.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuasv89l-yi76ev exit=${code}====="
exit "$code"
