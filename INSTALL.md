# Installation

## Prequisits

Python 3.x + virtualenv

### CentOS/RHEL 7.x (with EPEL enabled!)

```bash
yum install python34-virtualenv.noarch
```

## Checkout

~~~~bash
git clone https://git.linux-kernel.at/oliver/ivatar.git
cd ivatar
~~~~

## Virtual environment

~~~~bash
virtualenv -p python3 .virtualenv 
source .virtualenv/bin/activate
pip install -r requirements.txt
~~~~

## (SQL) Migrations

```bash
./manage migrate
```

## Collect static files

```bash
./manage.py collectstatic -l --no-input
```

## Run local (development) server

```bash
./manage.py runserver 0:8080 # or any other free port
```

## Create superuser (optional)

```bash
./manage.py createsuperuser # Follow the instructions
```

## Running the testsuite
```
./manage.py test -v3 # Or any other verbosity level you like
```

# Production deployment Webserver (non-cloudy)

To deploy this Django application with WSGI on Apache, NGINX or any other web server, please refer to the the webserver documentation; There are also plenty of howtos on the net (I'll not LMGTFY...)

# Production deloyment (cloudy)

## Red Hat OpenShift (Online)

There is already a file called create.sh, which can be reused to create an OpenShift online instance of ivatar. However, you need to have the correct environment variables set, as well as a working oc installation.

## Amazon AWS

Pretty sure this work as well; As OpenShift (Online).

I once wrote an Django (1.x) application in 2016, that used AWS. It can be found here:
[Gewusel from ofalk @ GitHub](https://github.com/ofalk/gewusel)
There is a file called ebcreate.txt as well as a directory called .ebextensions, which you need to check out in order to get an idea of how to deploy the application on AWS.

## Database

It should work with SQLite (do *not* use in production!), MySQL/MariaDB, as well as PostgreSQL.