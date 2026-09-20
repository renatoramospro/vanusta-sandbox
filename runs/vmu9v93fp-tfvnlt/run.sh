#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmu9v93fp-tfvnlt====="
(
  set -e
  python 'container.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmu9v93fp-tfvnlt exit=${code}====="
exit "$code"
