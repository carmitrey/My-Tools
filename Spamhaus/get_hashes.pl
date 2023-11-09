use Digest::SHA qw(sha256);
use MIME::Base32 ();

# this code assumes that the URL to be processed is in the $url variable, eg:
# $url = "http://catchall.hbltest.com/testdir1/testdir2/Test";
# match parts of the URL

open my $fh, '<', 'urls.txt' or die "Could not open file 'urls.txt' $!";
open my $out, '>', 'hashes.txt' or die "Could not open file 'output.txt' $!";

while (my $url = <$fh>) {
    my ($proto, $hostpart, $path) = $url =~ m{
        ^(\w+://)?      # optional protocol
        ([^/]*)         # host part, including optional authentication and port
        (/.*)           # path
    }x;
    return if !$hostpart;
    if ( defined($proto) and $proto !~ m{^(https?|ftp)://} ) {
        # not a hashable URL scheme
        return;
    }
    $hostpart =~ s/^.*\@//;   # remove optional authentication
    my $host = lc $hostpart;
    my ($yamlkey) = $host =~ /^([^:]+)/;
    # undo encoding of %-encoded characters
    $path =~ s/%([0-9a-f]{2})/chr hex $1/gei;
    # the $path_re and $lowerhash are hardcoded here, normally taken from the YAML file.
    # The $yamlkey can be used as the key for a lookup
    my $path_re = qr{^$|^[?].*|^[#].*|[^#?]+};
    my $lowerhash = 1;
    my ($matched_path) = $path =~ /^($path_re)/
        or return;
    $matched_path = lc $matched_path if $lowerhash;
    my $hash = MIME::Base32::encode( sha256($host . $matched_path) );

    print $out "$url\tHASH => $hash\n\n";
}

close $fh;
close $out;

my $python_script_path = "check_hashes.py";
my $result = system("python3 $python_script_path");

if ($result == 0) {
    print "Python script ran successfully\n";
} else {
    print "Python script failed\n";
}