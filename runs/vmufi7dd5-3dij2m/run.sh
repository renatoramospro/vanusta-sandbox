#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmufi7dd5-3dij2m====="
(
  set -e
  python 'feature_flags.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmufi7dd5-3dij2m exit=${code}====="
exit "$code"
