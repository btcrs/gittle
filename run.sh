#!/bin/bash

CONTAINER_NAME=versioning

docker stop ${CONTAINER_NAME}  
docker rm ${CONTAINER_NAME}

docker build -t ${CONTAINER_NAME} .
docker run --rm -d --name=${CONTAINER_NAME} -p 80:5000 -v `pwd`/app:/code -w /code ${CONTAINER_NAME} python app.py
