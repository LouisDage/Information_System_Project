import click
import sqlalchemy

from flask.cli import with_appcontext
from flask_sqlalchemy_session import flask_scoped_session
from sqlalchemy import create_engine, MetaData, select
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.automap import automap_base, name_for_collection_relationship, name_for_scalar_relationship


# Les éléments suivants seront définis lorsque l'automap aura fait son
# travail...
db_session = None # crée une session avec l a base de données et à cahque commit et rollback, la transaction sera validée ou annulée mais on relancera une transaction pour continuer à  faire des transactions
Supervisor = None #on va créer des classes pour quelle corresponde à des tables grâce au mapping
SupplyChain = None 
Actor = None
ClientSupplier = None
DeliveryCommand = None

def connect_db(app):
    '''Connextion à la base de données via l'automap'''
    # click.echo("db.connect_db")
    if app.config['TRACE_MAPPING']:
        click.echo("DB mapping...")

    # ORM: correpondances nom de table => nom de classe
    model_map = { #quels sont les classes et les tables associées
        'supervisor': 'Supervisor ', # à gauche le nom de la table et à droite le nom de la classe
        'supply_chain': 'SupplyChain',
        'actor': 'Actor',
        'client_supplier': 'ClientSupplier',
        'delivery_command': 'DeliveryCommand'
    }

    # ORM: correpondances association => attribut
    relation_map = {
        'SupplyChain=>Supervisor(supervised_by)': 'supervisor',
        'Supervisor=>SupplyChain(supervised_by)': 'all_supplychains',
        'ClientSupplier=>Actor(to_client)': 'client',
        'Actor=>ClientSupplier(to_client)': 'all_clients_suppliers_as_client',
        'ClientSupplier=>Actor(to_supplier)': 'supplier',
        'Actor=>ClientSupplier(to_supplier)':'all_clients_suppliers_as_supplier',

    }

    url_de_connexion = app.config['SQLALCHEMY_DATABASE_URI']
    sqlalchemy_engine_echo = app.config['SQLALCHEMY_ENGINE_ECHO'] # voir dans configuration, permet de voir toutes les  requêtes  
    
    if app.config['TRACE_MAPPING']: #réalisé par l'automapper(toujours correct) et engine (ce qui a été fait par nous)
        click.echo("URL de connexion:" + url_de_connexion)

    engine = create_engine( # on crée le moteur de connexion
        url_de_connexion,
        # si True, pratique pour déboguer (mais très verbeux)
        echo=sqlalchemy_engine_echo,
        # pour disposer des fonctionnalités de la version 2.0
        future=True,
    )
    our_metadata = MetaData() # crée métadonnées via le moteur 
    our_metadata.reflect(engine, only=model_map.keys()) # récupère uniquement les informations concernant les clés de model map 
    # print("our_metadata: ok")
    Base = automap_base(metadata=our_metadata) #on contruit la base à partir d'une métadonnée
    
    class Supervisor(Base):
        __tablename__ = 'supervisor'

        def __str__(self): # quand utilisateur aura besoin dans un fichier log on retournera la chaîne d'affichage
            return f"Supervisor({self.id},{self.username})"
    
    class SupplyChain (Base):
        __tablename__ = 'supply_chain'

        def __str__(self): #quand utilisateur aura besoin dans un fichier log on retournera la chaîne d'affichage
            return f"SupplyChain({self.name},{self.id_supervisor})"

    class Actor(Base):
        __tablename__ = 'actor'

        all_suppliers = relationship(
            "Actor",
            collection_class=set,
            secondary="client_supplier",
            primaryjoin='and_(Actor.name_supply_chain==client_supplier.c.name_supply_chain, Actor.generic_name==client_supplier.c.name_client)',
            secondaryjoin='and_(Actor.name_supply_chain==client_supplier.c.name_supply_chain, Actor.generic_name==client_supplier.c.name_supplier)',
            viewonly=True,
            backref="all_clients",
        )

        all_clients_suppliers_as_supplier = relationship(
            "ClientSupplier",
            collection_class=set,
            foreign_keys="[ClientSupplier.name_supplier, ClientSupplier.name_supply_chain]",
            overlaps="all_clients_suppliers_as_client,supplier, client",
        )            
        
        all_clients_suppliers_as_client = relationship(
            "ClientSupplier",
            collection_class=set,
            foreign_keys="[ClientSupplier.name_client, ClientSupplier.name_supply_chain]",
            overlaps="all_clients_suppliers_as_supplier,client,supplier",
        )            
        
        def __str__(self): #quand utilisateur aura besoin dans un fichier log on retournera la chaîne d'affichage
             return f"Actor({self.firm_name},{self.generic_name},{self.name_supply_chain})"

    class ClientSupplier(Base):
        __tablename__ = 'client_supplier'
        
        client = relationship(
            "Actor",
            foreign_keys="[ClientSupplier.name_client, ClientSupplier.name_supply_chain]",
            overlaps="all_clients_suppliers_as_supplier,supplier,all_clients_suppliers_as_client",
        )
        supplier = relationship(
            "Actor",
            foreign_keys="[ClientSupplier.name_supplier, ClientSupplier.name_supply_chain]",
            overlaps="all_clients_suppliers_as_client,client, all_clients_suppliers_as_supplier",
        )
        
        def __str__(self):
            return f"ClientSupplier({self.name_client},{self.name_supplier})"
        
    class DeliveryCommand(Base):
        __tablename__ = 'delivery_command'

        def __str__(self): #quand utilisateur aura besoin dans un fichier log on retournera la chaîne d'affichage
             return f"DeliveryCommand({self.name_client},{self.name_supplier})"

         
    def map_names(type, orig_func):
        """fonction d'aide à la mise en correspondance"""
        def _map_names(base, local_cls, referred_cls, constraint): # aller chercher dans relation_map, la clé d'association
            auto_name = orig_func(base, local_cls, referred_cls, constraint)
            # la clé de l'association
            key = f"{local_cls.__name__}=>{referred_cls.__name__}({constraint.name})"
            # quelle correpondance ?
            if key in relation_map:
                # Yes, return it
                name = relation_map[key]
            else:
                name = auto_name
            if app.config['TRACE_MAPPING']:
                # affiche la relation créée (pour comprendre ce qui se passe)
                click.echo(f" {type:>10s}: {key} {auto_name} => {name}")
            return name

        return _map_names

    Base.prepare( # à partir des trois classes faire les associations pour relier les différents objets
		#Compléter les classes définies précédemment
        name_for_scalar_relationship=map_names('scalar', name_for_scalar_relationship),
        name_for_collection_relationship=map_names('collection', name_for_collection_relationship),
    )

    ## On rend les tables du modèle globales à ce module
    #for cls in [User, Post, Star]:
    #    cls.__table__.info = dict(bind_key='main')
    #    globals()[cls.__name__] = cls
    
    #On rend les tables du modèle globales à ce module
    for cls in [Supervisor, SupplyChain, Actor, ClientSupplier,DeliveryCommand]:
        cls.__table__.info = dict(bind_key='main')
        globals()[cls.__name__] = cls

    Session = sessionmaker( # on crée une session qui 
        bind=engine,
        future=True,
        class_=sqlalchemy.orm.Session
    )
    globals()['db_session'] = flask_scoped_session(Session, app) #interroger les bases de données dans les routes

    if app.config['TRACE_MAPPING']:
        click.echo("DB mapping done.")


@click.command("check-db")
@with_appcontext
def check_db_command():
    """Vérifie que le mapping vers la base de données fonctionne bien."""
    assert db_session is not None #Database Session vérifié qu'il est crée
    # A supprimer, être placer dans les tests
    ordre = select(Supervisor)
    alls = db_session.execute(ordre).scalars().all()
    for sv in alls:
        assert isinstance(sv, Supervisor)
        print(" "*1, sv)
        for sc in sv.all_supplychains:
            assert isinstance(sc, SupplyChain)
            print(" "*2, sc)
            for actor in sc.actor_collection:
                assert isinstance(actor, Actor)
                print(" "*3, actor)
                for client_supplier in actor.all_clients_suppliers_as_supplier:
                    assert isinstance(client_supplier, ClientSupplier)
                    print(" "*4, "is supplier via", client_supplier, " of client", client_supplier.client)
                for client_supplier in actor.all_clients_suppliers_as_client:
                    assert isinstance(client_supplier, ClientSupplier)
                    print(" "*4, "is client via", client_supplier, "of supplier", client_supplier.supplier)
                for client in actor.all_clients:
                    print(" "*4, "client:", client)
                for supplier in actor.all_suppliers:
                    print(" "*4, "supplier:", supplier)


def init_app(app): #initialiser le lien avec la base de donnée via l'application
    """Initialisation du lien avec la base de données"""

    if app.config['TRACE']:
        click.echo(f"SQLALCHEMY_DATABASE_URI: {app.config['SQLALCHEMY_DATABASE_URI']}")

    connect_db(app)

    app.cli.add_command(check_db_command) # on prévient qu'il y a une commande qui s'appelle checkdb