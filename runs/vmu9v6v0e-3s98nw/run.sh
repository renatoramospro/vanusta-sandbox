#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmu9v6v0e-3s98nw====="
(
  set -e
  python 'container.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmu9v6v0e-3s98nw exit=${code}====="
exit "$code"
