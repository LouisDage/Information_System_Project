from operator import and_
import os
import tempfile
import warnings
import re
from flask import session
from sqlalchemy import and_
#from beergame.db import Actor, ClientSupplier, Supervisor, SupplyChain
#from beergame.db import db_session, Supervisor, Actor, SupplyChain,ClientSupplier, DeliveryCommand
# Tests basiques de l'application

def test_01_config_testing(test_app):
    """Vérification de l'utilisation de la base de tests"""
    print("wololo")
    assert test_app.testing is True

# Test d'utilisation de la base de données
def test_01_consultation(db_objects):
    """Test d'accès à la base de données"""
    db_session, Supervisor, SupplyChain, Actor,ClientSupplier, DeliveryCommand = db_objects
    from sqlalchemy import select

    ordre = select(Supervisor) # Sélectionne tous les utilisateurs
    all_supervisors = db_session.execute(ordre).scalars().all() #on les transforme en objet 
    assert len(all_supervisors) == 3 #Dans les données tests populate .sql
    for supervisor in all_supervisors:
        assert isinstance(supervisor, Supervisor) # On check que nos objets sont bien du même type
        #for post in actor.all_posts:
        #    assert isinstance(post, Post)
        #for post in actor.all_starred_posts:
        #    assert isinstance(post, Post)
        #for star in actor.all_stars:
        #    assert isinstance(star, Star)

def test_02_create_and_delete_actor(db_objects):
    """Création et destruction d'un utilisateur dans la base de données"""
    db_session, Supervisor, SupplyChain, Actor, ClientSupplier, DeliveryCommand = db_objects
    from sqlalchemy import select

    actorname = "test actor"
    password = "aaa"
    # on vérifie que l'utilisateur n'existe pas
    db_supervisor = db_session.execute(select(Supervisor).where(Supervisor.username == actorname)).scalars().first()
    assert db_supervisor is None
    # on le crée en mémoire
    supervisor = Supervisor(username=actorname, password=password)
    assert isinstance(supervisor, Supervisor)
    # on le prépare à être créé dans le base
    db_session.add(supervisor)
    assert supervisor.id is None
    # on le crée réellement (on peut récuper son id automatique)
    db_session.flush() # permet de transférer les données que l'on a ajouté pour qu'il soit réellement dans la base
    assert supervisor.id is not None
    # on le cherche dans la base
    db_supervisor = db_session.execute(select(Supervisor).where(Supervisor.username == actorname)).scalars().first()
    assert db_supervisor is not None
    assert isinstance(db_supervisor, Supervisor)
    # on vérifie que l'ORM a bien fait son boulot (les deux objets sont les mêmes)
    assert supervisor is db_supervisor
    # on efface l'utilisateur
    db_session.delete(supervisor)
    db_session.flush()
    # on vérifie qu'il n'existe plus dans la base
    db_supervisor = db_session.execute(select(Supervisor).where(Supervisor.username == actorname)).scalars().first()
    assert db_supervisor is None
    # on annule la transaction
    db_session.rollback()

#Test login logout
def test_03_login_logout(db_objects, web_client):
    """Log in and out for an actor"""
    db_session, Supervisor, SupplyChain, Actor,ClientSupplier, DeliveryCommand = db_objects
    from sqlalchemy import and_, select
    response = web_client.post('/auth/login', 
        data={
                "username": "polo",
                "password" : "polo",
            })
    assert session["user_id"] == 1
    response = web_client.get('/auth/logout'),
    assert  session == {}

# Tests creation d'une partie
def test_01_create_supply_chain_without_name(web_client):
    from sqlalchemy import select
    # Try without being logged in
    response = web_client.post('/supervise/create')
    assert response.status_code == 302
    response_as_text = response.get_data(as_text=True)
    assert re.search("/auth/login", response_as_text) is not None
    response = web_client.post('/auth/login',
        data={
            "username": "polo",
            "password" : "polo",
        })
    response = web_client.post('/supervise/create')
    assert response.status_code == 200
    response_as_text = response.get_data(as_text=True)
    assert re.search("Un nom de supply chain est requis", response_as_text) is not None

def test_02_create_supply_chain_with_name(web_client):
    from sqlalchemy import select
    response = web_client.post('/auth/login',
        data={
            "username": "polo",
            "password" : "polo",
        })
    response = web_client.post('/supervise/create', data={
        "name": "",
    })
    assert response.status_code == 200
    response_as_text = response.get_data(as_text=True)
    assert re.search("Un nom de supply chain est requis", response_as_text) is not None

    response = web_client.post('/supervise/create', data={
        "name": "test_supply_chain",
    })
    assert response.status_code == 302


    response = web_client.post('/supervise/create', data={
        "name": "test_supply_chain",
    })
    assert response.status_code == 200
    response_as_text = response.get_data(as_text=True)
    assert re.search("déjà utilisé", response_as_text) is not None


#Beginning of the tests for the "join" route 
def test_02_join_game_without_name_supply_chain(db_objects, web_client):
    """User tries to join a game without providing the name of the supply chain. Test shows error"""
    db_session, Supervisor, Actor, SupplyChain,ClientSupplier, DeliveryCommand = db_objects
    from sqlalchemy import and_, select
    response = web_client.post('/play/join', 
        data={
                "name_supply_chain": "",
                "firmname": "toto_firm",
                "password": "toto_firm",

            })
    response_as_text = response.get_data(as_text=True)
    assert re.search('Le nom de la partie est obligatoire', response_as_text) is not None

def test_03_join_game_with_invalid_name_supply_chain(db_objects, web_client):
    """User tries to join a game while providing an invalid name of supply chain. Test shows error"""
    db_session, Supervisor, Actor, SupplyChain,ClientSupplier, DeliveryCommand = db_objects
    from sqlalchemy import and_, select
    response = web_client.post('/play/join', 
        data={
                "name_supply_chain": "blabla",
                "firmname": "toto_firm",
                "password": "toto_firm",
            })
    response_as_text = response.get_data(as_text=True)
    assert re.search("La partie ou le mot de passe n&#39;est pas valide.", response_as_text) is not None

def test_04_join_complete_game_with_valid_name_supply_chain(db_objects, web_client):
    """User tries to join a game while providing a valid name of supply chain, but the chain is complete.
    Test shows error"""
    db_session, Supervisor, Actor, SupplyChain,ClientSupplier, DeliveryCommand = db_objects
    from sqlalchemy import and_, select
    response = web_client.post('/play/join', 
        data={
                "name_supply_chain": "complete_chain",
                "firmname": "",
                "password": "",
            })
    response_as_text = response.get_data(as_text=True)
    print(response_as_text)
    assert re.search('Le nombre de joueur est complet.', response_as_text) is not None

def test_05_1st_join_valid_supply_chain(db_objects, web_client):
    """User tries to join a game while providing a valid name of supply chain """
    db_session, Supervisor, Actor, SupplyChain,ClientSupplier, DeliveryCommand = db_objects
    from sqlalchemy import and_, select
    response = web_client.post('/play/join', 
        data={
                "name_supply_chain": "test",
                "firmname": "",
                "password": "",
            })
    response_as_text = response.get_data(as_text=True)
    print (response_as_text)
    assert (response.status_code == 302)
    assert re.search('play/lobby', response_as_text) is not None


def test_06_join_valid_supply_chain_wrong_firmname(db_objects, web_client):
    """User tries to join a game while providing a valid name of supply chain. User provides wrong player name"""
    db_session, Supervisor, Actor, SupplyChain,ClientSupplier, DeliveryCommand = db_objects
    from sqlalchemy import and_, select
    response = web_client.post('/play/join',
        data={
                        "name_supply_chain": "test",
                        "firmname": "non_existing_firm",
                        "password": "mdp",
                    })
    response_as_text = response.get_data(as_text=True)
    print (response_as_text)
    assert re.search('Le mot de passe ou le nom d&#39;utilisateur est incorrect.', response_as_text) is not None


def test_07_join_game_with_wrong_password(db_objects, web_client):
    """User tries to join a game while providing a valid name of supply chain. The user enters an 
    existing firm but the password is wrong"""
    db_session, Supervisor, Actor, SupplyChain,ClientSupplier, DeliveryCommand = db_objects
    from sqlalchemy import and_, select
    response = web_client.post('/play/join',
        data={
                        "name_supply_chain": "test",
                        "firmname": "existing_firm",
                        "password": "mauvais_mdp",
                    })
    response_as_text = response.get_data(as_text=True)
    print (response_as_text)
    assert re.search('Le mot de passe ou le nom d&#39;utilisateur est incorrect.', response_as_text) is not None



def test_08_join_game_and_other_actors_are_not_ready(db_objects, web_client):
    """User tries to join a game while providing a valid name of supply chain. They provide
    right firmname and password but all the actors are not ready so they join
    the waiting room"""
    db_session, Supervisor, Actor, SupplyChain,ClientSupplier, DeliveryCommand = db_objects
    from sqlalchemy import and_, select
    response = web_client.post('/play/join',
        data={
                        "name_supply_chain": "test",
                        "firmname": "existing_firm",
                        "password": "toto",
                    })
    response_as_text = response.get_data(as_text=True)
    print (response_as_text)
    assert re.search('Joueurs prêts', response_as_text) is not None


def test_09_join_game_and_other_actors_are_ready(db_objects, web_client):
    """User tries to join a game while providing a valid name of supply chain. They provide
    right firmname and password and all the actors are all ready; they see the dashboard"""
    db_session, Supervisor, Actor, SupplyChain,ClientSupplier, DeliveryCommand = db_objects
    from sqlalchemy import and_, select
    response = web_client.post('/play/join',
        data={
                        "name_supply_chain": "complete_chain",
                        "firmname": "existing_firm",
                        "password": "polo",
                    },
                    )
    response_as_text = response.get_data(as_text=True)
    print (response_as_text)
    assert re.search('/play/player_game', response_as_text) is not None

#End of the tests for the "join" route 

def test_03_create_actors_of_supply_chain(db_objects, web_client):
    db_session, Supervisor, SupplyChain, Actor,ClientSupplier, DeliveryCommand = db_objects
    from sqlalchemy import and_, select
    response = web_client.post('/auth/login',
        data={
            "username": "polo",
            "password" : "polo",
        })
    response = web_client.post('/supervise/create', data={
        "name": "test_supply_chain",
    })
    ordre = select(Actor.generic_name).where(
        Actor.name_supply_chain=="test_supply_chain",
    )
    supply_chain_actor = db_session.execute(ordre).scalars().all()
    assert len(supply_chain_actor)== 15 

    actor_names = [
        "Infinite Supplier",
        "Rose Supplier 1",
        "Rose Supplier 2",
        "Magic Capsule Producer",
        "Central Distribution Center",
        "French Wholesaler",
        "German Wholesaler",
        "French Pharmacy 1",
        "French Pharmacy 2",
        "German Pharmacy 1",
        "German Pharmacy 2",
        "French Client 1",
        "French Client 2",
        "German Client 1",
        "German Client 2",
    ]
    for actor in supply_chain_actor:
        assert actor in actor_names
        actor_names.remove(actor)

    relation_between_actors = [
        {"client": "Rose Supplier 1", "supplier": "Infinite Supplier"},
        {"client": "Rose Supplier 2", "supplier": "Infinite Supplier"},
        {"client": "Magic Capsule Producer", "supplier": "Rose Supplier 1"},
        {"client": "Magic Capsule Producer", "supplier": "Rose Supplier 2"},
        {"client": "Central Distribution Center", "supplier": "Magic Capsule Producer"},
        {"client": "French Wholesaler", "supplier": "Central Distribution Center"},
        {"client": "German Wholesaler", "supplier": "Central Distribution Center"},
        {"client": "French Pharmacy 1", "supplier": "French Wholesaler"},
        {"client": "French Pharmacy 2", "supplier": "French Wholesaler"},
        {"client": "German Pharmacy 1", "supplier": "German Wholesaler"},
        {"client": "German Pharmacy 2", "supplier": "German Wholesaler"},
        {"client": "French Client 1", "supplier": "French Pharmacy 1"},
        {"client": "French Client 2", "supplier": "French Pharmacy 2"},
        {"client": "German Client 1", "supplier": "German Pharmacy 1"},
        {"client": "German Client 2", "supplier": "German Pharmacy 2"},
    ]
    ordre = select(ClientSupplier.name_client, ClientSupplier.name_supplier).where(
        ClientSupplier.name_supply_chain=="test_supply_chain",
    )
    supply_chain_relation = db_session.execute(ordre).all()
    for relation in relation_between_actors:
        assert (relation["client"],relation["supplier"]) in supply_chain_relation
        supply_chain_relation.remove((relation["client"],relation["supplier"]))
    assert len(supply_chain_relation) == 0

    commands_between_actors = [
        {"client": "Rose Supplier 1", "supplier": "Infinite Supplier"},
        {"client": "Rose Supplier 2", "supplier": "Infinite Supplier"},
        {"client": "Magic Capsule Producer", "supplier": "Rose Supplier 1"},
        {"client": "Magic Capsule Producer", "supplier": "Rose Supplier 2"},
        {"client": "Central Distribution Center", "supplier": "Magic Capsule Producer"},
        {"client": "French Wholesaler", "supplier": "Central Distribution Center"},
        {"client": "German Wholesaler", "supplier": "Central Distribution Center"},
        {"client": "French Pharmacy 1", "supplier": "French Wholesaler"},
        {"client": "French Pharmacy 2", "supplier": "French Wholesaler"},
        {"client": "German Pharmacy 1", "supplier": "German Wholesaler"},
        {"client": "German Pharmacy 2", "supplier": "German Wholesaler"},
        {"client": "French Client 1", "supplier": "French Pharmacy 1"},
        {"client": "French Client 2", "supplier": "French Pharmacy 2"},
        {"client": "German Client 1", "supplier": "German Pharmacy 1"},
        {"client": "German Client 2", "supplier": "German Pharmacy 2"},
    ]
    ordre = select(DeliveryCommand.name_client, DeliveryCommand.name_supplier).where(
        DeliveryCommand.name_supply_chain=="test_supply_chain",
    )
    supply_chain_initial_commands = db_session.execute(ordre).all()
    for command in commands_between_actors:
        assert (command["client"], command["supplier"]) in supply_chain_initial_commands
        supply_chain_initial_commands.remove((command["client"], command["supplier"]))
    # 30 is 2* the number of relations between actors (deliveries and commands)
    assert len(supply_chain_initial_commands) == 30

# Test lobby supervisor

def test_01_check_supply_chain_name_on_lobby(web_client, db_objects):
    """
    Checks if the name of the supply_chain is written on the UI
    """
    from sqlalchemy import and_, select
    db_session, Supervisor, SupplyChain, Actor,ClientSupplier, DeliveryCommand = db_objects
    response = web_client.post('/auth/login',
        data={
            "username": "polo",
            "password" : "polo",
        })
    response = web_client.post('/supervise/create', data={
        "name": "test_supply_chain_name_displayed",
    }, follow_redirects=True)
    response_as_text = response.get_data(as_text=True)
    assert re.search("test_supply_chain_name_displayed", response_as_text)
    response = web_client.post('/supervise/create', data={
        "name": "another_test_supply_chain_name_displayed",
    }, follow_redirects=True)
    response_as_text = response.get_data(as_text=True)
    assert re.search("another_test_supply_chain_name_displayed", response_as_text)

def test_02_display_players_that_are_ready(web_client, db_objects):
    """
    Checks if the names of the players are displayed on screen.
    """
    from sqlalchemy import and_, select
    db_session, Supervisor, SupplyChain, Actor,ClientSupplier, DeliveryCommand = db_objects
    response = web_client.post('/auth/login',
        data={
            "username": "polo",
            "password" : "polo",
        })
    response = web_client.post('/supervise/join', data={
        "name_supply_chain": "complete_chain",
    }, follow_redirects=True)
    response_as_text = response.get_data(as_text=True)
    # Checks if we managed to connect to the right lobby
    assert re.search("complete_chain", response_as_text)
    assert re.search("toto_firm", response_as_text)
    assert re.search("toto_firm2", response_as_text)
    assert re.search("toto_firm3", response_as_text)
    assert re.search("existing_firm", response_as_text)
    assert re.search("toto_firm5", response_as_text)
    assert re.search("toto_firm6", response_as_text)
    assert re.search("toto_firm7", response_as_text)
    assert re.search("toto_firm8", response_as_text)
    assert re.search("toto_firm9", response_as_text)
    assert re.search("toto_firm10", response_as_text)
    assert re.search("toto_firm11", response_as_text)
    assert re.search("toto_firm12", response_as_text)
    assert re.search("toto_firm13", response_as_text)
    assert re.search("toto_firm14", response_as_text)
    assert re.search("toto_firm15", response_as_text)

# Tests Lobby player

def test_01_access_actor(db_objects):
    """Test d'accès à la base de données"""
    # On regarde ici si notre database contient bien toutes les classes que l'on souhaite
    db_session, Supervisor, SupplyChain, Actor, ClientSupplier,DeliveryCommand  = db_objects
    from sqlalchemy import select

    ordre = select(Actor)#.select_from(Actor).where((
    #    Actor.name_supply_chain=="test"
    #)) # Sélectionne tous les utilisateurs
    all_actors = db_session.execute(ordre).scalars().all() #on les transforme en objet 
    #print(all_actors)
    #assert len(all_actors) == 17 #Dans les données tests populate .sql
    for actor in all_actors:
        assert isinstance(actor, Actor) # On check que nos objets sont bien du même type

def test_02_add_free_actor(db_objects):
    """Complétion d'un actor dans la base de données"""
    db_session, Supervisor, SupplyChain ,Actor, ClientSupplier,DeliveryCommand = db_objects
    from sqlalchemy import select

    actorname = "test_firm"
    password = "aaa"
    name_supply_chain = "test"
    generic_name = 'Central Distribution Center'
    # on vérifie que tous les rôles n'ont pas encore été choisis
    db_actor = db_session.execute(
    select(Actor.generic_name)
    .select_from(Actor)
    .where(and_(Actor.firm_name == '',Actor.name_supply_chain==name_supply_chain, Actor.type=="player"))
    ).scalars().first()
    assert db_actor is not None
    # on le crée en mémoire
    actor = Actor(firm_name=actorname, password=password,name_supply_chain = name_supply_chain, type='player',generic_name = generic_name,initial_stock = 3)
    assert isinstance(actor, Actor)
    # on le prépare à être créé dans le base
    db_session.add(actor)
    # On l'enregistre dans la base de données
    db_session.flush() # permet de transférer les données que l'on a ajouté pour qu'il soit réellement dans la base
    assert actor.firm_name is not None
    # on le cherche dans la base
    db_actor = db_session.execute(select(Actor).where(and_(Actor.firm_name==actorname, Actor.password==password,Actor.name_supply_chain == name_supply_chain, Actor.type=='player',Actor.generic_name == generic_name,Actor.initial_stock == 3))).scalars().first()
    assert db_actor is not None
    assert isinstance(db_actor, Actor)
    # on vérifie que l'ORM a bien fait son boulot (les deux objets sont les mêmes)
    assert actor is db_actor
    # on efface l'utilisateur
    db_session.delete(actor)
    db_session.flush()
    # on vérifie qu'il n'existe plus dans la base
    db_actor = db_session.execute(select(Actor).where(and_(Actor.firm_name==actorname, Actor.password==password,Actor.name_supply_chain == name_supply_chain, Actor.type=='player',Actor.generic_name == generic_name,Actor.initial_stock == 3))).scalars().first()
    assert db_actor is None
    # on annule la transaction
    db_session.rollback()

#Series of tests on /lobby route for the player


def test_03_lobby_get_method(db_objects, web_client):
    """Test of the get method that renders the template lobby"""
    db_session, Supervisor, SupplyChain ,Actor, ClientSupplier,DeliveryCommand = db_objects
    from sqlalchemy import select
    response = web_client.get('/play/lobby',
        data={})
    response_as_text = response.get_data(as_text=True)
    print (response_as_text)
    assert re.search('Jeu en cours', response_as_text) is not None



def test_04_registering_lobby_with_unmatching_passwords(db_objects, web_client):
    """Series of tests on the /lobby route for post method. 
    This case: user enters unmatching passwords"""
    db_session, Supervisor, SupplyChain ,Actor, ClientSupplier,DeliveryCommand = db_objects
    from sqlalchemy import select
    response = web_client.post('/play/join', 
                                follow_redirects=True,
        data={
                "name_supply_chain": "test",
                "firmname": "",
                "password": "",
            })
    response_as_text = response.get_data(as_text=True)
    assert re.search("Jeu en cours", response_as_text)
    response = web_client.post('/play/lobby',
                                follow_redirects=True,
        data={
             "firmname" : "Roses",
            "password" : "beebou",
            "confirmedpassword" : "biibou",
        })
    response_as_text = response.get_data(as_text=True)
    assert re.search('Les mots de passe ne correspondent pas', response_as_text) is not None

def test_05_registering_lobby_without_firmname_or_without_password(db_objects, web_client):
    """Series of tests on the post method."""
    db_session, Supervisor, SupplyChain ,Actor, ClientSupplier,DeliveryCommand = db_objects
    from sqlalchemy import select
    
    #Join a game to identify the supply chain. Here it's the "test" SC 
    response = web_client.post('/play/join', 
                                follow_redirects=True,
        data={
                "name_supply_chain": "test",
                "firmname": "",
                "password": "",
            })
    
    #Test the case when the user doesn't enter a firmname at all
    #It ensures that this case scenario is taken into account
    response_as_text = response.get_data(as_text=True)
    assert re.search('Jeu en cours', response_as_text)
    response = web_client.post('/play/lobby',
                                follow_redirects=True,
        data={
            "firmname" : "",
            "password" : "beebou",
            "confirmedpassword" : "beebou",
        })
    response_as_text = response.get_data(as_text=True)
    print(response_as_text)
    assert re.search("Le nom d&#39;entreprise est obligatoire. ", response_as_text) is not None
    
    response = web_client.post('/play/lobby',
                                follow_redirects=True,
        data={
            "firmname" : "Roses",
            "password" : "",
            "confirmedpassword" : "",
        })
    response_as_text = response.get_data(as_text=True)
    print(response_as_text)
    assert re.search('Le mot de passe est obligatoire.', response_as_text) is not None

def test_06_registering_lobby_with_an_existing_firmname(db_objects, web_client):
    db_session, Supervisor, SupplyChain ,Actor, ClientSupplier,DeliveryCommand = db_objects
    from sqlalchemy import select
    response = web_client.post('/play/join', 
                                follow_redirects=True,
        data={
                "name_supply_chain": "test",
                "firmname": "",
                "password": "",
            })
    response_as_text = response.get_data(as_text=True)
    print(response_as_text)
    response = web_client.post('/play/lobby',
                                follow_redirects=True,
        data={
            "firmname" : "toto_firm",
            "password" : "mdps",
            "confirmedpassword" : "mdps",
        })

    response_as_text = response.get_data(as_text=True)
    print(response_as_text)
    assert re.search('Ce nom d&#39;entreprise a déjà été choisi.', response_as_text) is not None


def test_07_registering_lobby_actor_creation_check(db_objects, web_client):
    db_session, Supervisor, SupplyChain ,Actor, ClientSupplier,DeliveryCommand = db_objects
    from sqlalchemy import select
    response = web_client.post('/play/join', 
                                follow_redirects=True,
        data={
                "name_supply_chain": "test",
                "firmname": "",
                "password": "",
            })
    response = web_client.post('/play/lobby',
                                follow_redirects=True,
        data={
            "firmname" : "inexistant_firm",
            "actor" : "toto3",
            "password" : "mdp",
            "confirmedpassword" : "mdp",
        })
    response_as_text = response.get_data(as_text=True)
    ordre = select(db_objects[3].generic_name).where(
        db_objects[3].firm_name=="inexistant_firm",
    )
    found_generic_name = db_session.execute(ordre).all()
    assert re.search("toto3", found_generic_name[0].generic_name)


# On fait le test pour les étapes 1 et 4 de player_game

def test_01_access_step_1(web_client, db_objects):
    """Accès à l'étape 1 et on s'assure qu'une fois validé, 
    on ait les attributs 'seen_by_actor' qui soient à True"""
    db_session, Supervisor, SupplyChain ,Actor, ClientSupplier,DeliveryCommand = db_objects
    from sqlalchemy import select
    response = web_client.post('/play/join', 
        data={
                'name_supply_chain': 'test3',
                "firmname": 'toto_test3',
                "password": 'toto1',
            }, follow_redirects=True)
    response_as_text = response.get_data(as_text=True)
    assert (response.status_code == 200) # On est bien passé à la route suivante de la page du dashboard
    print(response_as_text)
    assert re.search('Réception des commandes des clients pour le round actuel', response_as_text)  
    # On va déterminer les clés du dictionnaire
    response = web_client.post('/play/player_game')
    assert (response.status_code == 302) #lorsque l'on met à jour (ajoute élément dans) la base de donnée

    seen_by_actor_player = db_session.execute(select(DeliveryCommand.seen_by_actor)
    .select_from(DeliveryCommand)
    .where(and_(DeliveryCommand.type=='command', 
    DeliveryCommand.name_supplier=='Magic Capsule Producer',
    DeliveryCommand.name_supply_chain == 'test3',
    ))
    ).scalars().first()
    # Si on reste à l'étape 1
    assert seen_by_actor_player == False

def test_01_fill_for_step_4(web_client, db_objects):
    """Accès à l'étape 4 et on s'assure qu'une fois validé, 
    on ait les commandes qui soient rentrées"""
    db_session, Supervisor, SupplyChain ,Actor, ClientSupplier,DeliveryCommand = db_objects
    from sqlalchemy import select
    # On va compléter momentanément à la main les tables
    # On est actuellement au round 2 
    
    # On va mettre les attributs des commandes à true d'une part

    seen_by_actor_all_players = db_session.execute(select(DeliveryCommand)
    .select_from(DeliveryCommand)
    .where(and_(DeliveryCommand.type=='command',
    DeliveryCommand.name_supply_chain=='test3',
    DeliveryCommand.round==1,
    DeliveryCommand.seen_by_actor==False))
    ).scalars().all()
    print(seen_by_actor_all_players)
    for seen in seen_by_actor_all_players:
        seen.seen_by_actor = True
    
    db_session.commit()

    # On va mettre les attributs des livraisons du 1er round à true d'une part

    seen_by_actor_all_players_deliveries = db_session.execute(select(DeliveryCommand)
    .select_from(DeliveryCommand)
    .where(and_(DeliveryCommand.type=='delivery',
    DeliveryCommand.name_supply_chain=='test3',
    DeliveryCommand.round==1,
    DeliveryCommand.seen_by_actor==False))
    ).scalars().all()
    print(seen_by_actor_all_players)
    for seens in seen_by_actor_all_players_deliveries:
        seens.seen_by_actor = True
    
    # On vérifie que les attributs sont à True
    seen_by_actor_all_players = db_session.execute(select(DeliveryCommand)
    .select_from(DeliveryCommand)
    .where(and_(DeliveryCommand.type=='command',
    DeliveryCommand.name_supply_chain=='test3',
    DeliveryCommand.round==1))
    ).scalars().all()

    for actor in seen_by_actor_all_players:
        assert actor.seen_by_actor==True

    # On va également ajouter des livraisons fictives et les mettre à True 

    client_supplier_link = db_session.execute(select(DeliveryCommand.name_client, DeliveryCommand.name_supplier)
    .select_from(DeliveryCommand)
    .where(and_(DeliveryCommand.type=='command',
    DeliveryCommand.name_supply_chain=='test3',
    DeliveryCommand.round==1))
    ).all()

    for client in client_supplier_link:
        delivery_valid = DeliveryCommand(type='delivery',
        name_client=client['name_client'],
        name_supplier=client['name_supplier'],
        round =2,
        quantity=2,
        seen_by_actor=False,
        name_supply_chain='test3')
        db_session.add(delivery_valid)
    db_session.commit()

    # On vérifie que les livraisons ont été correctement ajoutées
    client_supplier_link = db_session.execute(select(DeliveryCommand.name_client, DeliveryCommand.name_supplier)
    .select_from(DeliveryCommand)
    .where(and_(DeliveryCommand.type=='delivery',
    DeliveryCommand.name_supply_chain=='test3',
    DeliveryCommand.round==2))
    ).all()

    assert client_supplier_link is not None


def test_01_access_step_04(web_client,db_objects):
    db_session, Supervisor, SupplyChain ,Actor, ClientSupplier,DeliveryCommand = db_objects
    from sqlalchemy import select
    response = web_client.post('/play/join', 
    data={
        "name_supply_chain": "test3",
        "firmname": 'toto_test3',
        "password": 'toto1',
        },follow_redirects=True)
    response_as_text = response.get_data(as_text=True)
    assert (response.status_code == 200)
    print(response)
    supplier_players = db_session.execute(
        select(ClientSupplier.name_supplier)
        .select_from(ClientSupplier)
        .where(and_(ClientSupplier.name_supply_chain == 'test3', 
        ClientSupplier.name_client == 'Magic Capsule Producer'))
    ).all()

    # Une fois que l'on est sur la page player_task, on va réaliser les commandes
    response = web_client.post('/play/player_game', data = {
        "Rose Supplier 1":5,
        "Rose Supplier 2":4
    })
    print(response)
    assert (response.status_code == 302) #lorsque l'on met à jour (ajoute élément dans) la base de donnée

# Test for reset the firm_name and password of player

def test_01_reset_player_firmname_password(web_client,db_objects):
    db_session, Supervisor, SupplyChain ,Actor, ClientSupplier,DeliveryCommand = db_objects
    from sqlalchemy import select

    response = web_client.post('/auth/login', 
    data={
        "username": "toto_step",
        "password": 'toto1',
        },follow_redirects=True)
    response_as_text = response.get_data(as_text=True)
    assert (response.status_code == 200)
    print(response_as_text)
    assert re.search("Vous êtes connecté", response_as_text) is not None

    response = web_client.get('/supervise/join')
    response_as_text = response.get_data(as_text=True)
    assert(response.status_code == 200)

    response = web_client.post('/supervise/join',data={"name_supply_chain":'test3'})
    response_as_text = response.get_data(as_text=True)
    assert(response.status_code == 302)

    response = web_client.post('/supervise/reset_one_actor',data={"reset":'German Wholesaler'})
    response_as_text = response.get_data(as_text=True)
    assert(response.status_code == 302)

    actor_German_Wholesaler_firmname = db_session.execute(select(Actor.firm_name)
    .select_from(Actor)
    .where(Actor.generic_name == 'German Wholesaler')
    .where(Actor.name_supply_chain == 'test3')
    ).scalars().first()

    actor_German_Wholesaler_password= db_session.execute(select(Actor.password)
    .select_from(Actor)
    .where(Actor.generic_name == 'German Wholesaler')
    .where(Actor.name_supply_chain == 'test3')
    ).scalars().first()

    assert actor_German_Wholesaler_firmname == ''
    assert actor_German_Wholesaler_password == ''

# Test pour accéder au graphiques

def test_01_access_graphics(web_client,db_objects):
    db_session, Supervisor, SupplyChain ,Actor, ClientSupplier,DeliveryCommand = db_objects
    from sqlalchemy import select

    response = web_client.post('/auth/login', 
    data={
        "username": "toto_step",
        "password": 'toto1',
        })
    response_as_text = response.get_data(as_text=True)
    assert (response.status_code == 302)
    #print(response_as_text)
    #assert re.search("Vous êtes connecté", response_as_text) is not None

    response = web_client.get('/supervise/join')
    response_as_text = response.get_data(as_text=True)
    assert(response.status_code == 200)

    response = web_client.post('/supervise/join',data={"name_supply_chain":'test3'})
    response_as_text = response.get_data(as_text=True)
    assert(response.status_code == 302)

    response = web_client.get('/supervise/dashboard')
    response_as_text = response.get_data(as_text=True)
    assert(response.status_code == 200)

    response = web_client.get('/supervise/graphs')
    response_as_text = response.get_data(as_text=True)
    assert(response.status_code == 200)
