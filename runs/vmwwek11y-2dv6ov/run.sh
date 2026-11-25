#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmwwek11y-2dv6ov====="
(
  set -e
  python 'build_system.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmwwek11y-2dv6ov exit=${code}====="
exit "$code"
