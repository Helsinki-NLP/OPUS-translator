#!/bin/sh

PATHTO=../models/tokenizer
PATHPBE=../models/bpe_codes/bpe50000.train.fi

echo $1 |\
    $PATHTO/replace-unicode-punctuation.perl |\
    $PATHTO/remove-non-printing-char.perl |\
    $PATHTO/normalize-punctuation.perl -l $2 |\
    $PATHTO/tokenizer.perl -q -no-escape -l $2 |\
    sed 's/  */ /g;s/^ *//g;s/ *$$//g' |\
    subword-nmt apply-bpe -c $PATHPBE
