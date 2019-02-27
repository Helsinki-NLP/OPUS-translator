#!/usr/bin/perl -w

use strict;

my $corpus = $ARGV[0];
my $l1 = $ARGV[1];
my $l2 = $ARGV[2];
my $out = $ARGV[3];

print STDERR "de-xml.perl: processing $corpus.$l1 & .$l2 to $out\n";

open(F,"$corpus.$l1");
open(E,"$corpus.$l2");
open(FO,">$out.$l1");
open(EO,">$out.$l2");

my $i=0;

while(my $f = <F>) {
  my $e = <E>;
  $i++;
  chop($e); chop($f);
  next if ($e =~ /^<.+>$/) && ($f =~ /^<.+>$/);
  if (($e =~ /^<.+>$/) || ($f =~ /^<.+>$/)) {
    print STDERR "MISMATCH[$i]: $e <=> $f\n";
    next;
  }
  if (($e =~ /<.+>/) || ($f =~ /<.+>/)) {
      print STDERR "TAGS IN TEXT, STRIPPING[$i]: $e <=> $f\n";
      $e =~ s/ *<[^>]+> */ /g;
      $e =~ s/^ +//;
      $e =~ s/ +$//;
      $f =~ s/ *<[^>]+> */ /g;
      $f =~ s/^ +//;
      $f =~ s/ +$//;
      print STDERR "TAGS STRIPPED: $e <=> $f\n";
  }

  print FO $f."\n";
  print EO $e."\n";
}
