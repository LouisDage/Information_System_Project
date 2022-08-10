# Installing the virual environnement
In the phase-3/application directory create a new virtualenv :
`bash
virtualenv venv-desperalbi
`

Activate the virtualenv
`bash
source venv-desperalbi/bin/activate
`

Install the packages
`bash
pip install -e .
`
# Initialize the database

Create the user beergameadmin with the password beergameadminpass
`bash
sudo su - postgres -c "createuser --pwprompt beergameadmin"
`

For the password enter : beergameadminpass

Create an empty database named beergame
`bash
sudo su - postgres -c "createdb --owner beergameadmin beergame"
`

Create the tables necessary for running the application
`bash
psql postgresql://beergameadmin:beergameadminpass@localhost:5432/beergame < beergame/schema-postgresql.sql
`

# Initialize the test database 

Create an empty databate named beergame-test
`bash
sudo su - postgres -c "createdb --owner beergameadmin beergame-test"
`

Create the tables necessary for running the tests
`bash
psql postgresql://beergameadmin:beergameadminpass@localhost:5432/beergame-test < beergame/schema-postgresql.sql
`

Populate the database with our test data
`bash
psql postgresql://beergameadmin:beergameadminpass@localhost:5432/beergame-test < beergame/schema-postgresql-test.sql
`

# Accessing the DataBase

To access the database use the following bash command :
`bash
psql postgresql://beergameadmin:beergameadminpass@localhost:5432/beergame
`

# Start Flask application
Set up environment variable
Create a new file .flaskenv at the root of your project
Copy paste the following lines:

`
# Name of the Flask application
FLASK_APP=beergame

# The environment in which it is executed (development, test, production...)
FLASK_ENV=test\
FLASK_ENV=production\
FLASK_ENV=development

# The name of the file and the name of the application configuration
FLASKRPG_SETTINGS=instance.configurations:config
FLASKRPG_CONFIG=development

# The name of the file and the name of the application configuration
FLASKBEERGAME_SETTINGS=instance.configurations:config
FLASKBEERGAME_CONFIG=development
`


Start the flask server
`bash
flask run
`


