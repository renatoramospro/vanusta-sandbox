#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvoepojj-dbeu7t====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvoepojj-dbeu7t exit=${code}====="
exit "$code"
