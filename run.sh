#!/bin/bash

command=$1
runner=$2
params=$3

CONTAINER_NAME=versioning
docker stop ${CONTAINER_NAME}
#docker rm ${CONTAINER_NAME}
#docker build -t ${CONTAINER_NAME} .

if [[ ${command} == makedocs ]]; then
<<<<<<< Updated upstream
  docker run --rm -d --name=${CONTAINER_NAME} -p 8000:8000 -v `pwd`:/code -w /code/docs ${CONTAINER_NAME} make html
elif [[ ${command} == coverage ]]; then
  docker run --rm -it --name=${CONTAINER_NAME} -p 8000:8000 -v `pwd`:/code -w /code ${CONTAINER_NAME} /bin/sh -c 'cd ./app && coverage run --source=./ manage.py test'
elif [[ ${command} == run ]]; then
  docker run --rm -it --name=${CONTAINER_NAME} -p 8000:8000 -v `pwd`/app:/code -w /code ${CONTAINER_NAME} python manage.py ${runner} ${params}
elif [[ ${command} == runserver ]]; then
  docker run --rm -it --name=${CONTAINER_NAME} -p 8000:8000 -v `pwd`/app:/code -w /code ${CONTAINER_NAME} python manage.py runserver [::]:8000
elif [[ ${command} == coverage ]]; then
  docker run --rm -it --name=${CONTAINER_NAME} -p 8000:8000 -v `pwd`/app:/code -w /code ${CONTAINER_NAME} coverage run ./manage.py test
=======
  docker run --rm -d --name=${CONTAINER_NAME} -p 8008:8008 -v `pwd`:/code -w /code/docs ${CONTAINER_NAME} make html
elif [[ ${command} == run ]]; then
  docker run --rm -it --name=${CONTAINER_NAME} -p 8008:8008 -v `pwd`/app:/code -w /code ${CONTAINER_NAME} python manage.py ${runner}
elif [[ ${command} == runserver ]]; then
  docker run --rm -it --name=${CONTAINER_NAME} -p 8008:8008 -v `pwd`/app:/code -w /code ${CONTAINER_NAME} python manage.py runserver [::]:8008
>>>>>>> Stashed changes
else
  docker run --rm -it --name=${CONTAINER_NAME} -p 8008:8008 -v `pwd`/app:/code -w /git_code/app ${CONTAINER_NAME} python manage.py runserver [::]:8008
fi
