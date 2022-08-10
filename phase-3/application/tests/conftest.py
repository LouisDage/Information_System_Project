# initialisation des tests effectués par 'pytest' dans ce répertoire (et
# ses sous-répertoires)
import os
import pytest
import warnings
import subprocess

SQLALCHEMY_DATABASE_URI_TEST = "postgresql://beergameadmin:beergameadminpass@localhost:5432/beergame-test" # pour la suntaxe SQLAlchemy, il faut définir une url de la base car il faut qu'elle soit initaliser avant la création de l'application pour les tests

def execute_sql_file_with_psql(url, filename): #permettre d'utiliser un fichier SQL et l'exécuter automatiquement, initialiser la structure de base de données et la peupler
    """Exécute un script SQL via psql en utilisant l'URL fourni pour se connecter"""
    psql_url = url.replace("+psycopg2","")
    #warnings.warn(psql_url)
    #warnings.warn(filename)
    res = subprocess.run(
        ['/usr/bin/psql', '-f', filename, psql_url],
        capture_output=True,
        encoding="utf-8",
        timeout=3,
    )
    if res.stdout != '' :
        warnings.warn(f"\nSTDOUT: {res.stdout}")
    if res.stderr != '' :
        warnings.warn(f"\nSTDERR: {res.stderr}")
    assert res.returncode == 0

#Les trios fonctions ci dessous fournissent au test des objets sur lesquels ils vont pouvoir effectuer des tests
@pytest.fixture(autouse=True, scope="session")
def init_test_db():
    """(ré)Initialisation de la structure et des données de la base de test"""
    execute_sql_file_with_psql(SQLALCHEMY_DATABASE_URI_TEST, "beergame/schema-postgresql.sql")
    execute_sql_file_with_psql(SQLALCHEMY_DATABASE_URI_TEST, "beergame/schema-postgresql-test.sql")
    return True


@pytest.fixture
def test_app(): #fabrique l'application de test
    """L'application Flask de test de flaskrpg"""
    os.environ["FLASKBEERGAME_CONFIG"] = "testing"
    print("wesh?")
    from beergame import create_app
    print("wesh")
    test_app = create_app({
        'TESTING': True,
        #"SQLALCHEMY_DATABASE_URI": SQLALCHEMY_DATABASE_URI_TEST,
        #"TRACE": True,
        #"TRACE_MAPPING": True,
    })
    yield test_app #équivalent de return

@pytest.fixture
def web_client(test_app):
    """Un client Web pour simuler des requêtes provenant d'un navigateur"""
    with test_app.test_client() as web_client: #web client = client test
        yield web_client

@pytest.fixture
def db_objects(test_app): #objets pour accéder aux bases de donnée
    """Tous les objets pour l'accès à la base de données"""
    from sqlalchemy import text
    from beergame.db import db_session, Supervisor, Actor, SupplyChain,ClientSupplier, DeliveryCommand
    yield (db_session, Supervisor, SupplyChain,Actor, ClientSupplier, DeliveryCommand)
    #db_session.close()
    #engine = db_session.get_bind()
    #engine.dispose()
