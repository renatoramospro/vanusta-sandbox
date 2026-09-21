#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuatas2s-ouv16r====="
(
  set -e
  python 'replay_system_secure.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuatas2s-ouv16r exit=${code}====="
exit "$code"
