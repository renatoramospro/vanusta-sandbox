#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwwt85ju-gisavx====="
(
  set -e
  python 'benchmark.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwwt85ju-gisavx exit=${code}====="
exit "$code"
