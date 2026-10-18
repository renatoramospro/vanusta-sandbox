#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmvd2u5z5-ll1ygp====="
(
  set -e
  python 'main.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmvd2u5z5-ll1ygp exit=${code}====="
exit "$code"
