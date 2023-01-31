# Voteaire Engine

TODO: fill me out

# Development

for development, it's recommended that you use a virtual environment. To create a virtual environment called .venv and install prerequisited run:
```BASH
# create
python -m venv .venv

# activate
.venv\Scripts\activate.bat #Windows
.venv/bin/activate #linux

# install prereqs

pip install -r requirements.txt
```

# Running
To run during development simply do the following:

```
cd src
python app.py
```
# Running a mock server for frontend development
```
connexion run src/openapi/openapi-spec.yml --mock=all --debug
```

# Migration
In order to make things easy for us when trying to migrate our database, we are using a python library called [Flask-Migrate](https://flask-migrate.readthedocs.io/en/latest/index.html). It allows you to easily create migration scripts and upgrade the db by typing simple commands.

## Initializing
Before anything else, you will need to install it using pip.

```bash
pip install Flask-Migrate
```

After the first step, if we do not have a migrations folder in src/ yet, we need to create one. We can do this by executing the following command:

```bash
flask db init
```

## Actually migrating
Now that we have everything ready, we can start registering our migrations. This can be done with the following command:

```bash
flask db migrate -m "Migration Message"
```

Finally, if we want to actually turn those migrations into reality, we can execute the following command:

```bash
flask db upgrade
```

The `flask db migrate` command should be used whenever we change a developer changes the database schema, while the `flask db upgrade` command should be used to actually apply the changes made by yourself or other developers to an existing db with an older schema.

To generate the raw sql file, you can execute `flask db upgrade --sql`
