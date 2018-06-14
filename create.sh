#!/bin/sh

oc new-project ivatar
# Take care, the following environment variable must be set either in bashrc/profile or locally in this session
oc secrets new-basicauth lkernat-gitlab-openshift-falko-access-token --password=$LKERNAT_GITLAB_OPENSHIFT_ACCESS_TOKEN
oc secrets add serviceaccount/builder secrets/lkernat-gitlab-openshift-falko-access-token
MYSQL_PASSWORD=`openssl rand -base64 16`
MYSQL_ROOT_PASSWORD=`openssl rand -base64 16`
oc new-app --source-secret=lkernat-gitlab-openshift-falko-access-token \
  python~https://git.linux-kernel.at/oliver/ivatar.git \
  mysql-persistent \
  --group=python+mysql-persistent \
  -e MYSQL_USER=ivatar \
  -p MYSQL_USER=ivatar \
  -e MYSQL_PASSWORD=$MYSQL_PASSWORD \
  -p MYSQL_PASSWORD=$MYSQL_PASSWORD \
  -e MYSQL_DATABASE=ivatar \
  -p MYSQL_DATABASE=ivatar \
  -e MYSQL_ROOT_PASSWORD=$MYSQL_ROOT_PASSWORD \
  -p MYSQL_ROOT_PASSWORD=$MYSQL_ROOT_PASSWORD \
  -e IVATAR_MAILGUN_API_KEY=$IVATAR_MAILGUN_API_KEY \
  -e IVATAR_MAILGUN_SENDER_DOMAIN=$IVATAR_MAILGUN_SENDER_DOMAIN
oc expose svc/ivatar
