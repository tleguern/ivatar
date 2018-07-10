#!/bin/sh

oc new-project ivatar

DB_PASSWORD=`openssl rand -base64 16`
DB_ROOT_PASSWORD=`openssl rand -base64 16`

if [ -n "$USE_MYSQL" ]; then
  DB_CMDLINE="mysql-persistent
  --group=python+mysql-persistent
  -e MYSQL_USER=ivatar
  -p MYSQL_USER=ivatar
  -e MYSQL_PASSWORD=$DB_PASSWORD
  -p MYSQL_PASSWORD=$DB_PASSWORD
  -e MYSQL_DATABASE=ivatar
  -p MYSQL_DATABASE=ivatar
  -e MYSQL_ROOT_PASSWORD=$DB_ROOT_PASSWORD
  -p MYSQL_ROOT_PASSWORD=$DB_ROOT_PASSWORD"
else
  DB_CMDLINE="postgresql-persistent
  -e POSTGRESQL_USER=ivatar
  -p POSTGRESQL_USER=ivatar
  -e POSTGRESQL_DATABASE=ivatar
  -p POSTGRESQL_DATABASE=ivatar
  -e POSTGRESQL_PASSWORD=$DB_PASSWORD
  -p POSTGRESQL_PASSWORD=$DB_PASSWORD
  -e POSTGRESQL_ADMIN_PASSWORD=$DB_ROOT_PASSWORD"
fi

if [ -n "$LKERNAT_GITLAB_OPENSHIFT_ACCESS_TOKEN" ]; then
    oc secrets new-basicauth lkernat-gitlab-openshift-falko-access-token --password=$LKERNAT_GITLAB_OPENSHIFT_ACCESS_TOKEN
    oc secrets add serviceaccount/builder secrets/lkernat-gitlab-openshift-falko-access-token
    SECRET_CMDLINE="--source-secret=lkernat-gitlab-openshift-falko-access-token"
fi

oc new-app $SECRET_CMDLINE python~https://git.linux-kernel.at/oliver/ivatar.git \
  -e IVATAR_MAILGUN_API_KEY=$IVATAR_MAILGUN_API_KEY \
  -e IVATAR_MAILGUN_SENDER_DOMAIN=$IVATAR_MAILGUN_SENDER_DOMAIN \
  $DB_CMDLINE

oc expose svc/ivatar
