#!/bin/bash

command=$1

CONTAINER_NAME=versioning
docker stop ${CONTAINER_NAME}  
docker rm ${CONTAINER_NAME}
docker build -t ${CONTAINER_NAME} .

if [[ ${command} == makedocs ]]; then
  docker run --rm -d --name=${CONTAINER_NAME} -p 8000:8000 -v `pwd`:/code -w /code/docs ${CONTAINER_NAME} make html
else
  docker run --rm -it --name=${CONTAINER_NAME} -p 8000:8000 -v `pwd`/app:/code -w /git_code/app ${CONTAINER_NAME} python manage.py runserver [::]:8000
  #docker run --rm -it --name=${CONTAINER_NAME} -p 8000:8000 -v `pwd`/app:/code -w /code ${CONTAINER_NAME} python manage.py runserver [::]:8000
fi
