#!/bin/sh

echo "inside shell script"
echo "\$1 is $1"
echo "\$USER is $USER"
echo "this is a test $(date)" > /home/$USER/test.txt
#echo "printing env:"
#env
echo "last line in shell script"