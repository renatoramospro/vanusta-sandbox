#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmubpjlky-l7zptx====="
(
  set -e
  python 'gitops_engine.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmubpjlky-l7zptx exit=${code}====="
exit "$code"
