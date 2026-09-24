#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmufj6461-fjwchh====="
(
  set -e
  python 'feature_flags_secure.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmufj6461-fjwchh exit=${code}====="
exit "$code"
