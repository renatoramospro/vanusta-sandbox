#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmub6hnv6-yktkur====="
(
  set -e
  python 'animation_engine.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmub6hnv6-yktkur exit=${code}====="
exit "$code"
