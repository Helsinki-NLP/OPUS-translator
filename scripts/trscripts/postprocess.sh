#!/bin/sh

echo $1 |\
    /home/cloud-user/multi30k-dataset/scripts/moses-3a0631a/tokenizer/detokenizer.perl -q |\
    sed 's/\@\@ //g'
