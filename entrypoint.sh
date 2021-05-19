#!/bin/bash
umask 000
if [ -z "$1" ]
  then
    /usr/local/bin/spoonbill --help
    /bin/bash
  else
    /usr/local/bin/spoonbill "$@"
fi
