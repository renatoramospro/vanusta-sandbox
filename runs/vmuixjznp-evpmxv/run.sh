#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuixjznp-evpmxv====="
(
  set -e
  python 'myers_engine.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuixjznp-evpmxv exit=${code}====="
exit "$code"
