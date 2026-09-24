#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmufkw5rx-nnh7le====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmufkw5rx-nnh7le exit=${code}====="
exit "$code"
