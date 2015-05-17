#!/bin/bash

# This current directory. Assumes the setup.sh script is in the "aeco" folder directly.
DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

pip install -r $DIR/requirements.txt

if ! [ -f $DIR/aeco.ini ]; then
    cp $DIR/aeco.ini.example $DIR/aeco.ini
    echo "Please configure the paths in $DIR/aeco.ini! Otherwise aeco/joyent will not work entirely."
fi

which aeco > /dev/null

if [ $? -eq 1 ]; then
    echo "you can install aeco globally by adding this line to your PATH, e.g. in your .bash_profile "
    echo "     export PATH=\$PATH:$DIR"
fi