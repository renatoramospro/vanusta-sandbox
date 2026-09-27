#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuk0kcyv-qzi40i====="
(
  set -e
  python 'slab_allocator.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuk0kcyv-qzi40i exit=${code}====="
exit "$code"
