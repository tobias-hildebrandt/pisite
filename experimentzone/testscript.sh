#!/bin/sh

echo "inside shell script"
echo "current user is $USER"
echo "this is a test $(date)" > /home/$USER/test.txt
#echo "printing env:"
#env
echo "last line in shell script"
echo "END"