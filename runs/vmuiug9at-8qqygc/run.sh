#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuiug9at-8qqygc====="
(
  set -e
  python 'migration_engine.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuiug9at-8qqygc exit=${code}====="
exit "$code"
