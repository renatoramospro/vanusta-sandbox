#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvskjgfx-oc7exk====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvskjgfx-oc7exk exit=${code}====="
exit "$code"
