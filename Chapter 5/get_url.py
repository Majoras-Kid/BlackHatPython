import urllib2

body = urllib2.urlopen("https://www.nostarch.com/")

print body.read()