#!/bin/sh

PATHTO=`cat /home/cloud-user/secrets/tokenizerpath`
PATHBPE=`cat /home/cloud-user/secrets/bpepath`

echo $1 | $PATHTO/lowercase.perl | $PATHTO/normalize-punctuation.perl -l en | $PATHTO/tokenizer.perl -l en -q -threads 2 | subword-nmt apply-bpe -c $PATHBPE
