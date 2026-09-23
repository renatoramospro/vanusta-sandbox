#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmudyl3k6-n1wsci====="
(
  set -e
  python 'documenter_engine.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmudyl3k6-n1wsci exit=${code}====="
exit "$code"
