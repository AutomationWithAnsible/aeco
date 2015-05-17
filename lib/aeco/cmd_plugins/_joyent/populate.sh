#!/bin/bash
[ $(basename $(pwd)) != "joyent" ] && echo "Can only run from within 'cmd_plugins/joyent' directory" && exit 1
for dc  in "us-east-1" "us-west-1"  "us-sw-1"  "eu-ams-1" "us-east-2" "us-east-3"
do
    echo "Populating $dc"
    export SDC_URL=https://$dc.api.joyentcloud.com
    sdc-listimages > ${dc}.images.json
    sdc-listpackages > ${dc}.package.json
    sdc-listnetworks > ${dc}.networks.json
done

# Custom DC
for dc  in "eu-nue-1"
do
    echo "Populating $dc"
    export SDC_URL=https://10.63.15.43
    sdc-listimages > ${dc}.images.json
    sdc-listpackages > ${dc}.package.json
    sdc-listnetworks > ${dc}.networks.json
done