#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuabfhv0-cvwcqg====="
(
  set -e
  python 'progression_sim.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuabfhv0-cvwcqg exit=${code}====="
exit "$code"
