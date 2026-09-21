#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuawyazm-o3wss7====="
(
  set -e
  python 'localization_system.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuawyazm-o3wss7 exit=${code}====="
exit "$code"
