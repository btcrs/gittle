#!/bin/bash

CONTAINER_NAME=versioning

docker stop ${CONTAINER_NAME}  
docker rm ${CONTAINER_NAME}

docker build -t ${CONTAINER_NAME} .
docker run --rm -it --name=${CONTAINER_NAME} -p 8000:8000 -v `pwd`/app:/code -w /code ${CONTAINER_NAME} python manage.py runserver [::]:8000
