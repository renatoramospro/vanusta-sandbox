#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuiw5sru-wot9cg====="
(
  set -e
  python 'event_sourcing_engine.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuiw5sru-wot9cg exit=${code}====="
exit "$code"
