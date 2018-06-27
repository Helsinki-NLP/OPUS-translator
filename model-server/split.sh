#!/bin/sh

PATHSPL=`cat /home/cloud-user/secrets/splitpath`

echo $1 | $PATHSPL/split-sentences.perl -q
