#!/bin/sh

PATHTO="/home/cloud-user/multi30k-dataset/scripts/moses-3a0631a/tokenizer"

echo $1 | $PATHTO/lowercase.perl | $PATHTO/normalize-punctuation.perl -l en | $PATHTO/tokenizer.perl -l en -q -threads 2 | subword-nmt apply-bpe -c /home/cloud-user/subwordtest/de-en.bpe20000
