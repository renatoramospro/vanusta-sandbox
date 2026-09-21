#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmub6phdc-1i107h====="
(
  set -e
  python 'animation_engine.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmub6phdc-1i107h exit=${code}====="
exit "$code"
