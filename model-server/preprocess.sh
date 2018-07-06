#!/bin/sh

PATHTO=`cat secrets/tokenizerpath`
PATHBPE=`cat secrets/bpepath`

echo $1 | $PATHTO/lowercase.perl | $PATHTO/normalize-punctuation.perl -l en | $PATHTO/tokenizer.perl -l en -q -threads 2 | subword-nmt apply-bpe -c $PATHBPE
