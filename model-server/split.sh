#!/bin/sh

PATHSPL=`cat secrets/splitpath`

echo $1 | $PATHSPL/split-sentences.perl -q
