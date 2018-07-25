#!/bin/sh

PATHTO=`cat secrets/danosv_tokenizer`
PATHPBE=`cat secrets/bpe_sv`

echo $1 |\
    $PATHTO/replace-unicode-punctuation.perl |\
    $PATHTO/remove-non-printing-char.perl |\
    $PATHTO/normalize-punctuation.perl -l $2 |\
    $PATHTO/tokenizer.perl -no-escape -l $2 |\
    sed 's/  */ /g;s/^ *//g;s/ *$$//g' |\
    subword-nmt apply-bpe -c /home/cloud-user/models/bpe_codes/bpe50000.train.sv
