#!/bin/bash
helpFunction()
{
   echo ""
   echo "Usage: $0 PATH"
   echo -e "\tPATH path to the destination dir"
   exit 1 # Exit script after printing help
}

if [ -z "$1" ]
  then
    helpFunction
fi

if [ -f "$1/website/siteconfig.json" ]; then
    # UPDATE existing
    echo "Updating instance ..."
    rsync -avu --exclude={'data','website/siteconfig.json','website/config.js','make_instance.sh'} ${PWD}/* $1
    $1/website/adminscripts/init_or_update.py
else 
    echo "Initialize new instance ..."
    echo ${PWD} > $1/INSTANCE_PATH.txt
    rsync -avu --exclude={'data','website/siteconfig.json','website/config.js','make_instance.sh'} ${PWD}/* $1
    cat ${PWD}/website/siteconfig.json.template | sed "s#%{path}#$1/website#g" > $1/website/siteconfig.json
	cp ${PWD}/website/config.js.template $1/website/config.js
    mkdir $1/data
    $1/website/adminscripts/init_or_update.py
    chown -R apache: $1/data
    chmod -R g+rwX $1/data
fi
