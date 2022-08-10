import os 
import click
import sys

from flask import Flask
from werkzeug.utils import import_string

def create_app(test_config=None):
    """Create and configure an instance of the Flask application."""
    app = Flask(__name__, instance_relative_config=True)

        #click.echo(config[os.environ["FLASKRPG_CONFIG"]])
    configs = import_string(os.environ["FLASKBEERGAME_SETTINGS"]) # dans le fichier .flaskenv
    app.config.from_object(configs[os.environ["FLASKBEERGAME_CONFIG"]])

    if app.config['TRACE']:
        click.echo("create_app:" + __name__)
        click.echo("SQLALCHEMY_DATABASE_URI is: " + app.config["SQLALCHEMY_DATABASE_URI"])
      # register the database commands
    from beergame import db

    db.init_app(app)

    from beergame import auth, supervise,play,index

    app.register_blueprint(auth.bp)
    app.register_blueprint(supervise.bp)
    app.register_blueprint(play.bp)
    app.register_blueprint(index.bp)
    app.add_url_rule('/', endpoint='index') # index représente la page d'accueil, c'est grâce à cela que l'on peut mettre dans le url_for juste index et pas forcément le bluprints associé.
 
    return app





