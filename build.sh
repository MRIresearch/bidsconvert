#!/bin/bash
WORKDIR=$PWD

VCS_REF=01201122
BUILD_DATE=$(date +%F)
VERSION=2.1.4
IMVER=0.2
docker build -t  orbisys/bidsconvert:${IMVER} --build-arg BUILD_DATE=${BUILD_DATE} --build-arg VERSION=${VERSION} --build-arg VCS_REF=${VCS_REF} .

docker push  orbisys/bidsconvert:${IMVER}
