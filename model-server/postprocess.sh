#!/bin/sh

PATHTO=`cat /home/cloud-user/secrets/tokenizerpath`

echo $1 | $PATHTO/detokenizer.perl -q
