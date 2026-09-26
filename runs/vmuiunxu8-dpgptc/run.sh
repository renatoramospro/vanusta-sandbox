#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuiunxu8-dpgptc====="
(
  set -e
  python 'migration_engine.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuiunxu8-dpgptc exit=${code}====="
exit "$code"
