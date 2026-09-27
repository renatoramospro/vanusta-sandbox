#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmukcgi8c-9pvd3u====="
(
  set -e
  python 'chaos_framework.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmukcgi8c-9pvd3u exit=${code}====="
exit "$code"
