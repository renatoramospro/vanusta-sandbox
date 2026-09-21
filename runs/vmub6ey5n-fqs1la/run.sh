#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmub6ey5n-fqs1la====="
(
  set -e
  python 'animation_engine.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmub6ey5n-fqs1la exit=${code}====="
exit "$code"
