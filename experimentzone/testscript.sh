#!/bin/sh

echo "inside shell script"
echo "\$USER is $USER"
echo "this is a test $(date)" > /home/$USER/test.txt
#echo "printing env:"
#env
echo "last line in shell script"