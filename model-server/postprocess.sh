#!/bin/sh

PATHTO=`cat secrets/tokenizerpath`

echo $1 | $PATHTO/detokenizer.perl -q
