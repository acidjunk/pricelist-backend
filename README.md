[![Build Status](https://travis-ci.com/acidjunk/pricelist-backend.svg?branch=master)](https://travis-ci.com/acidjunk/pricelist-backend)

# pricelist-backend

Pricelist backend MVP

The REST API server for a pricelist service

An online demo can be found on: https://api.prijslijst.info
If you want to see what you can build with it, grab a free account on: https://www.prijslijst.info/register

## Running it locally

Setup a decent python 3 env (it should work from 3.6 upwards):

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements/all.txt
```

## When deploying with zappa

Currently, the best version to use is python39

## Configuration

The project relies on an "env" file to set ENVIRONMENT vars like the correct DB settings etc. An Example env file:

```
DATABASE_URI=postgres://pricelist:pricelist@localhost/pricelist
SECURITY_PASSWORD_SALT=some_salt
SECRET_KEY=fancy_long_secret_key
FLASK_DEBUG=1
DEBUG=1
PYTHON_PATH=.
FLASK_APP=main
```

So go ahead and create it, now the only thing left is to setup a postgres users. Without going into a lot of postgres
details:

```
createuser -U postgres -sP pricelist
createdb -U postgres pricelist
```

You can now run migrations to get an empty DB or import an existing DB:

```
psql -U postgres -d pricelist < your_db_dump.psql
```

Start the webserver with:
```
./start.sh
```

## Handy stuff

Test login stuff from CLI:

```bash
PYTHONPATH=. PASSWORD=yourpass EMAIL=admin@example.com python client_examples/login.py
```

## Deploy notes

Python 3.9 for now.

Take care to manually install psycopg-binary as described in improviser README.md
Note: A list of exact deps is avail in `requirements/`
