#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmua467tf-tvnaw5====="
(
  set -e
  python 'circuit_breaker_mission.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmua467tf-tvnaw5 exit=${code}====="
exit "$code"
