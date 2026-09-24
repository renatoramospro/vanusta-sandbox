#!/usr/bin/env bash
echo "=====VANUSTA-BEGIN-vmuez8huj-eqdkun====="
(
  set -e
  python 'websocket_doc_generator_v3.py'
) 2>&1
code=$?
echo "=====VANUSTA-END-vmuez8huj-eqdkun exit=${code}====="
exit "$code"
