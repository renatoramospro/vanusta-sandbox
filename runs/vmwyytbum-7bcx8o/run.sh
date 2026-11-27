#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwyytbum-7bcx8o====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwyytbum-7bcx8o exit=${code}====="
exit "$code"
