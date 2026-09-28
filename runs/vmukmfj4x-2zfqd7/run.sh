#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmukmfj4x-2zfqd7====="
(
  set -e
  python 'experiment_cqrs.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmukmfj4x-2zfqd7 exit=${code}====="
exit "$code"
