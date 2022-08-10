import random
import functools
from math import *
from crypt import methods
from curses import BUTTON2_CLICKED
from random import randint
import io

from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, session
)
#from werkzeug.security import (check_password_hash, generate_password_hash )
#from werkzeug.exceptions import abort
from sqlalchemy import select, and_ , func

from beergame.db import DeliveryCommand, Supervisor, db_session, SupplyChain, Actor, ClientSupplier
from beergame.step import *
from beergame.function_util import *
from beergame.graphs import graph
from beergame.auth import login_required
from beergame.utils import (
    get_all_players_from_one_supply_chain,
    create_new_supply_chain,
    create_all_actors_for_a_supply_chain,
    create_relationship_between_actors,
    to_int,
    get_tracking_sheet_data
)



bp = Blueprint("supervise", __name__, url_prefix="/supervise")

PLAYER_NAMES = [
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
]
RELATION_BETWEEN_ACTORS= [
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

@bp.before_app_request
def load_supply_chain_name():
    """If a user id is stored in the session, load the user object from
    the database into ``g.user``."""
    name_supply_chain = session.get("name_supply_chain")

    if name_supply_chain is None:
        g.name_supply_chain = None
    else:
        g.name_supply_chain = db_session.execute(
            select(SupplyChain)
            .where(SupplyChain.name == name_supply_chain)
        ).scalars().first()


def name_supply_chain_required(view):
    """View decorator that redirects anonymous users to the login page."""

    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.name_supply_chain is None:
            return redirect(url_for("supervise.join_supervisor"))

        return view(**kwargs)

    return wrapped_view

@bp.route("/create", methods=("GET", "POST"))
@login_required
def create():
    """Create a new supply chain.

    Validates that the supply chain name is not already taken.
    """
    if request.method == "POST":
        name_supply_chain= request.form.get("name", '').strip()

        error = ""

        if name_supply_chain == '':
            error += "Un nom de supply chain est requis."


        preexistant_supply_chain = db_session.execute(
            select(SupplyChain).
            where(SupplyChain.name == name_supply_chain)
        ).scalars().first()
        if preexistant_supply_chain is not None:
            error += f"Le nom de partie {name_supply_chain} est déjà utilisé. "

        if error == '':
            create_new_supply_chain(name_supply_chain)
            create_all_actors_for_a_supply_chain(name_supply_chain)
            db_session.commit()
            create_relationship_between_actors(name_supply_chain)
            db_session.commit()
            session["name_supply_chain"] = name_supply_chain
            return redirect(url_for("supervise.lobby"))
        flash(error)
    return render_template("supervise/create.html")

@bp.route("/change_initial_state", methods=("GET", "POST"))
@login_required
@name_supply_chain_required
def change_initial_state():
    """
    Returns the page to change the initial state of the supply chain
    Or changes its initial parameters in the DB.
    """
    error = ""
    try:
        name_supply_chain = session["name_supply_chain"]
    except KeyError:
        error+="Vous n'êtes pas le superviseur de la partie."
        return render_template("index.html")
    else:
        if request.method == "POST":
            # Change the initial stock
            list_new_initial_stock = []
            # 10 = nombre d'acteurs de la chaine, à changer plus tard
            for actor_number in range(10):
                list_new_initial_stock.append(
                    request.form.get(
                        f"initial_stock_{actor_number+1}"
                    )
                )
            for index_new_initial_stock in range(len(list_new_initial_stock)):
                if list_new_initial_stock[index_new_initial_stock] != '':
                    db_session.query(Actor).\
                    filter(Actor.name_supply_chain==name_supply_chain).\
                    filter(Actor.generic_name==PLAYER_NAMES[index_new_initial_stock]).\
                    update({"initial_stock":list_new_initial_stock[index_new_initial_stock]})
                    db_session.commit()

            # Change the relations between actors
            list_new_relation = []
            # 11 = nombre de relations modifiables de la chaine, à changer plus tard
            for relation_number in range(11):
                new_relation = {
                    "initial_command": request.form.get(f"initial_command_{relation_number+1}"),
                    "command_time": request.form.get(f"command_time_{relation_number+1}"),
                    "delivery_time": request.form.get(f"delivery_time_{relation_number+1}"),
                }
                list_new_relation.append(new_relation)
            for index_new_relation in range(len(list_new_relation)):
                # Get from the form the new values for command_time, delivery_time & quantity
                new_command_time = to_int(list_new_relation[index_new_relation]["command_time"])
                new_delivery_time = to_int(list_new_relation[index_new_relation]["delivery_time"])
                new_quantity = to_int(list_new_relation[index_new_relation]["initial_command"])
                # Get from the DB the old values for command_time, delivery_time & quantity
                old_relation = db_session.query(ClientSupplier).\
                    filter(ClientSupplier.name_client==RELATION_BETWEEN_ACTORS[index_new_relation]["client"]).\
                    filter(ClientSupplier.name_supplier==RELATION_BETWEEN_ACTORS[index_new_relation]["supplier"]).\
                    filter(ClientSupplier.name_supply_chain==name_supply_chain)
                old_command_time = old_relation[0].command_time
                old_delivery_time = old_relation[0].delivery_time
                old_command = db_session.query(DeliveryCommand).\
                    filter(ClientSupplier.name_client==RELATION_BETWEEN_ACTORS[index_new_relation]["client"]).\
                    filter(ClientSupplier.name_supplier==RELATION_BETWEEN_ACTORS[index_new_relation]["supplier"]).\
                    filter(ClientSupplier.name_supply_chain==name_supply_chain)
                old_quantity = old_command[0].quantity
                # If no number was in the form, new_delivery_time = old_delivery_time
                if not new_delivery_time:
                    new_delivery_time = old_delivery_time
                    # If no number was in the form, new_command_time = old_command_time
                if not new_command_time:
                    new_command_time = old_command_time
                    # If no number was in the form, new_quantity = old_quantity
                if not new_quantity:
                    new_quantity = old_quantity
                    # If either command_time or delivery_time changed, change the relation in the DB
                if (new_command_time != old_command_time) or (new_delivery_time != old_delivery_time):
                    db_session.query(ClientSupplier).\
                            filter(ClientSupplier.name_client==RELATION_BETWEEN_ACTORS[index_new_relation]["client"]).\
                            filter(ClientSupplier.name_supplier==RELATION_BETWEEN_ACTORS[index_new_relation]["supplier"]).\
                            filter(ClientSupplier.name_supply_chain==name_supply_chain).\
                            update({
                                "delivery_time":new_delivery_time,
                                "command_time":new_command_time,
                            })

                # Add new commands that didn't exist before
                if new_command_time + new_delivery_time > old_command_time + old_delivery_time:
                    for round_new_delivery in range(
                        old_command_time+old_delivery_time,
                        new_command_time+new_delivery_time
                    ):
                        new_delivery=DeliveryCommand(
                            name_client=RELATION_BETWEEN_ACTORS[index_new_relation]["client"],
                            name_supply_chain=name_supply_chain,
                            name_supplier=RELATION_BETWEEN_ACTORS[index_new_relation]["supplier"],
                            type="delivery",
                            round=round_new_delivery,
                            quantity=new_quantity,
                        )
                        db_session.add(new_delivery)
                        new_command=DeliveryCommand(
                            name_client=RELATION_BETWEEN_ACTORS[index_new_relation]["client"],
                            name_supply_chain=name_supply_chain,
                            name_supplier=RELATION_BETWEEN_ACTORS[index_new_relation]["supplier"],
                            type="command",
                            round=round_new_delivery-old_command_time,
                            quantity=new_quantity,
                        )
                        db_session.add(new_command)
                    db_session.commit()

                # Delete commands that no longer occur
                if old_command_time + old_delivery_time > new_command_time + new_delivery_time:
                    for round_delivery_to_delete in range(
                        new_command_time+new_delivery_time,
                        old_command_time+old_delivery_time
                    ):
                        db_session.query(DeliveryCommand).\
                                filter(DeliveryCommand.name_supply_chain==name_supply_chain).\
                                filter(DeliveryCommand.name_client==RELATION_BETWEEN_ACTORS[index_new_relation]["client"]).\
                                filter(DeliveryCommand.name_supplier==RELATION_BETWEEN_ACTORS[index_new_relation]["supplier"]).\
                                filter(DeliveryCommand.round==round_delivery_to_delete-old_delivery_time+1).\
                                filter(DeliveryCommand.type=="delivery").\
                                delete()
                        db_session.query(DeliveryCommand).\
                                filter(DeliveryCommand.name_supply_chain==name_supply_chain).\
                                filter(DeliveryCommand.name_client==RELATION_BETWEEN_ACTORS[index_new_relation]["client"]).\
                                filter(DeliveryCommand.name_supplier==RELATION_BETWEEN_ACTORS[index_new_relation]["supplier"]).\
                                filter(DeliveryCommand.round==round_delivery_to_delete-old_delivery_time-old_command_time+1).\
                                filter(DeliveryCommand.type=="command").\
                                delete()
                    db_session.commit()

                # Change the round of already created deliveries
                if new_delivery_time!=old_delivery_time or new_command_time!=old_command_time:
                    list_deliveries = db_session.query(DeliveryCommand).\
                            filter(DeliveryCommand.name_client==RELATION_BETWEEN_ACTORS[index_new_relation]["client"]).\
                            filter(DeliveryCommand.name_supplier==RELATION_BETWEEN_ACTORS[index_new_relation]["supplier"]).\
                            filter(DeliveryCommand.name_supply_chain==name_supply_chain).\
                            filter(DeliveryCommand.type=="delivery").\
                            order_by(DeliveryCommand.round)
                    for delivery in list_deliveries:
                        db_session.query(DeliveryCommand).\
                                filter(DeliveryCommand.round==delivery.round).\
                                filter(DeliveryCommand.name_client==RELATION_BETWEEN_ACTORS[index_new_relation]["client"]).\
                                filter(DeliveryCommand.name_supplier==RELATION_BETWEEN_ACTORS[index_new_relation]["supplier"]).\
                                filter(DeliveryCommand.name_supply_chain==name_supply_chain).\
                                filter(DeliveryCommand.type=="delivery").\
                                update({"round":delivery.round+(old_delivery_time-new_delivery_time)})

                    # Change the round of already created commands
                    list_commands = db_session.query(DeliveryCommand).\
                            filter(DeliveryCommand.name_client==RELATION_BETWEEN_ACTORS[index_new_relation]["client"]).\
                            filter(DeliveryCommand.name_supplier==RELATION_BETWEEN_ACTORS[index_new_relation]["supplier"]).\
                            filter(DeliveryCommand.name_supply_chain==name_supply_chain).\
                            filter(DeliveryCommand.type=="command").\
                            order_by(DeliveryCommand.round)
                    for command in list_commands:
                        db_session.query(DeliveryCommand).\
                                filter(DeliveryCommand.round==command.round).\
                                filter(DeliveryCommand.name_client==RELATION_BETWEEN_ACTORS[index_new_relation]["client"]).\
                                filter(DeliveryCommand.name_supplier==RELATION_BETWEEN_ACTORS[index_new_relation]["supplier"]).\
                                filter(DeliveryCommand.name_supply_chain==name_supply_chain).\
                                filter(DeliveryCommand.type=="command").\
                                update({"round":command.round+(old_delivery_time-new_delivery_time)+(old_command_time-new_command_time)})
                    db_session.commit()

                # Changes the quantity of all the commands and deliveries to the new value
                if new_quantity != old_quantity:
                    db_session.query(DeliveryCommand).\
                    filter(DeliveryCommand.name_client==RELATION_BETWEEN_ACTORS[index_new_relation]["client"]).\
                    filter(DeliveryCommand.name_supplier==RELATION_BETWEEN_ACTORS[index_new_relation]["supplier"]).\
                    filter(DeliveryCommand.name_supply_chain==name_supply_chain).\
                    update({"quantity":new_quantity})
                    db_session.commit()

            actors=get_all_players_from_one_supply_chain(session["name_supply_chain"])
            return render_template("supervise/lobby.html", actors=actors)
        return render_template("supervise/change_initial_state.html", actors=PLAYER_NAMES, relations=RELATION_BETWEEN_ACTORS[:-4])


@bp.route("/lobby", methods=("GET", "POST"))
@login_required
@name_supply_chain_required
def lobby():
    name_supply_chain = session['name_supply_chain']
    if request.method == "POST":
        pass
    actors=get_all_players_from_one_supply_chain(session["name_supply_chain"])
    return render_template("supervise/lobby.html", actors=actors)

@bp.route("/dashboard", methods=("GET","POST"))
@login_required
@name_supply_chain_required
def dashboard():
    # On récupère les données de la session
    name_supply_chain = session['name_supply_chain']
    
    #On récupère la liste des acteurs
    actor = db_session.execute(
    select(Actor.generic_name)
    .select_from(Actor)
    .where(and_(Actor.firm_name != '',Actor.name_supply_chain==name_supply_chain, Actor.type=="player"))
    ).all()

    # On récupère la liste des joueurs de la partie
    all_players = get_all_players_from_one_supply_chain(session["name_supply_chain"]).all()

    # Nombre de lignes dans la table Delivery_Command 
    nber_lines_delivery_command=get_nber_lines_delivery_command(name_supply_chain)

    # Nombre de relations clients_fournisseurs
    nber_clients_suppliers=get_nber_clients_suppliers(name_supply_chain)

    #On récupère le numéro du round actuel
    current_round = floor(nber_lines_delivery_command / (2*nber_clients_suppliers)) + 1

    #On créé cette valeur pour pas avoir la problème de data 
    post=0

    # Pour l'étape 1 et 2 si toutes les commandes des joueurs ont été envoyées
    if nber_lines_delivery_command % (2 * nber_clients_suppliers) == 0:
        for player in all_players:
            name_player=player['generic_name']
            # On récupère les demandes clients du joueur
            client_demands=get_client_demands(name_supply_chain,current_round,name_player)
            # Si un joueur n'a pas encore validé ses commandes on est à l'étape 1
            if client_demands[0]['seen_by_actor'] == False:
                etape = 1 
                break
            # Si tous les joueurs ont validé leurs commandes
            else:
                etape = 2
    else:
        etape = 2
    
    # Pour l'étape 3 et 4 si tous les livraisons des joueurs ont été reçues
    if nber_lines_delivery_command % (2 * nber_clients_suppliers) >= nber_clients_suppliers:
        for player in all_players:
            name_player=player['generic_name']

            # On récupère les livraisons du joueur
            client_deliveries=get_client_deliveries(name_supply_chain,current_round,name_player)

            # Si un joueur n'a pas encore validé ses livraisons on est à l'étape 3
            if client_deliveries[0]['seen_by_actor'] == False:
                etape = 3 
                break
            # Si tous les joueurs ont validé leurs livraisons
            else:
                etape = 4

    list_player_ready = []
    # vérifié
    if etape == 1:
        for player in all_players:
            ready_player = {}
            # On récupère les demandes clients du joueur
            name_player=player['generic_name']
            client_demands=get_client_demands(name_supply_chain,current_round,name_player)
            
            # Si un joueur n'a pas encore validé ses commandes on est à l'étape 1
            if client_demands[0]['seen_by_actor'] == False:
                ready_player['ready'] = False
                ready_player['name_actor'] = player['generic_name']
            else:
                ready_player['ready'] = True
                ready_player['name_actor'] = player['generic_name']
            list_player_ready.append(ready_player)
    # Étape 2
    if etape == 2:
        #On vérifie que les joueurs ont rentré leurs livraisons
        for player in all_players:
            ready_player = {}
            name_player=player['generic_name']

            # Nombre de clients du joueur
            nber_suppliers_player=get_nber_suppliers_player(name_supply_chain,name_player)

            # On vérifie si les livraisons n'ont pas déjà été rentrées
            nber_delivery_existant=get_nber_delivery_exist(name_supply_chain,current_round,name_player)

             # On vérifie si les lignes ont été validées déjà par le joueur
            if nber_delivery_existant == nber_suppliers_player:
                ready_player['ready'] =  True
                ready_player['name_actor'] = player['generic_name']
            else:
                ready_player['ready'] =  False
                ready_player['name_actor'] = player['generic_name']
            list_player_ready.append(ready_player)
    # Étape 3
    if etape == 3:
        for player in all_players:
            ready_player = {}
            name_player=player['generic_name']
            # On récupère les livraisons qui vont être reçues par le joueur 
            client_deliveries=get_client_deliveries(name_supply_chain,current_round,name_player)

            if client_deliveries[0]['seen_by_actor'] == False:
                ready_player['ready'] = False
                ready_player['name_actor'] = player['generic_name']
            else:
                ready_player['ready'] = True
                ready_player['name_actor'] = player['generic_name']
            list_player_ready.append(ready_player)

    # Étape 4 sûr que ça marche
    if etape == 4 :

        for player in all_players:
            ready_player = {}
            name_player=player['generic_name']
            # Nombre de fournniseurs du joueur
            nber_suppliers_player=get_nber_suppliers_player(name_supply_chain,name_player)


            # On vérifie si les commandes n'ont pas déjà été rentrées
            nber_command_existant=get_nber_command_exist(name_supply_chain,current_round,name_player)


             # On vérifie si les lignes ont été validées déjà par le joueur
            if nber_command_existant == nber_suppliers_player:
                ready_player['ready'] =  True
                ready_player['name_actor'] = player['generic_name']
            else:
                ready_player['ready'] =  False
                ready_player['name_actor'] = player['generic_name']
            list_player_ready.append(ready_player)
    
    # On récupère les données pour les graphs 
 
    list_player_rest_penalty, list_player_rest_penalty_cumulated, list_player_stock_penalty, list_player_stock_penalty_cumulated, round_list, nber_round, list_player_stock_and_rest_penalty, list_player_stock_and_rest_penalty_cumulated = graph(name_supply_chain) 
    # On check si la partie est terminée ou pas 

    state_game1 = db_session.execute( # Pour changer l'état du bouton, True si la partie est finie 
    select(SupplyChain.end_game) 
    .select_from(SupplyChain) 
    .where(and_(SupplyChain.name == name_supply_chain)) 
    ).scalars().first()
    
    if request.method=='POST':
        if request.form.get("actor_name")!=None:
            post=1
            generic_name=request.form.get("actor_name",'')
            data=get_tracking_sheet_data(generic_name)
            return render_template("supervise/dashboard.html", list_player_ready=list_player_ready,list_player_rest_penalty=list_player_rest_penalty, list_player_rest_penalty_cumulated=list_player_rest_penalty_cumulated, list_player_stock_penalty=list_player_stock_penalty, list_player_stock_penalty_cumulated=list_player_stock_penalty_cumulated, round_list=round_list, nber_round=nber_round, list_player_stock_and_rest_penalty=list_player_stock_and_rest_penalty, list_player_stock_and_rest_penalty_cumulated=list_player_stock_and_rest_penalty_cumulated,state_game=state_game1,data=data,post=post,actor=actor,etape=etape)
            
        else:
            if etape==4:

            
                nber_command_existant_german_client_1=get_nber_command_exist(name_supply_chain,
                current_round,'German Client 1')
                nber_command_existant_german_client_2=get_nber_command_exist(name_supply_chain,
                current_round,'German Client 2')
                nber_command_existant_french_client_1=get_nber_command_exist(name_supply_chain,
                current_round,'French Client 1')
                nber_command_existant_french_client_2=get_nber_command_exist(name_supply_chain,
                current_round,'French Client 2')
                
                if [nber_command_existant_german_client_1,nber_command_existant_german_client_2,nber_command_existant_french_client_1,nber_command_existant_french_client_2]==[0,0,0,0]:
                    clients=['German Client 1','German Client 2','French Client 1','French Client 2']
                    suppliers=['German Pharmacy 1','German Pharmacy 2','French Pharmacy 1','French Pharmacy 2']

                    for i in range(len(clients)):
                        new_delivery_command = DeliveryCommand(
                        type='command',
                        name_supplier=suppliers[i],
                        name_supply_chain = name_supply_chain,
                        name_client = clients[i],
                        round = current_round,
                        quantity = request.form.get(clients[i], ''),
                        seen_by_actor = False
                        )
                        db_session.add(new_delivery_command)
                    
                    db_session.commit() 
    return render_template("supervise/dashboard.html",post=post, list_player_ready=list_player_ready,list_player_rest_penalty=list_player_rest_penalty, list_player_rest_penalty_cumulated=list_player_rest_penalty_cumulated, list_player_stock_penalty=list_player_stock_penalty, list_player_stock_penalty_cumulated=list_player_stock_penalty_cumulated, round_list=round_list, nber_round=nber_round, list_player_stock_and_rest_penalty=list_player_stock_and_rest_penalty, list_player_stock_and_rest_penalty_cumulated=list_player_stock_and_rest_penalty_cumulated,state_game=state_game1, actor=actor,etape=etape)

        
 
@bp.route("/join", methods=("GET", "POST"))
@login_required
def join():
    if request.method == "POST" :
        name_supply_chain = request.form.get("name_supply_chain")
        session["name_supply_chain"] = name_supply_chain
        return redirect(url_for("supervise.lobby"))
    else :
        games = db_session.execute(
            select(SupplyChain.name)
            .where(
            SupplyChain.id_supervisor==session["user_id"],
            )
        ).all()
        return render_template("supervise/join.html", games=games)

@bp.route("/reset_one_actor", methods = ("POST",))
@login_required
@name_supply_chain_required
def reset_one_actor():
    
    # On récupère le nom générique de l'actor que l'on veut réinitialiser 
    actor_reinitialized = request.form.get("reset", '').strip()

    actor_to_change = db_session.execute(select(Actor)
    .select_from(Actor)
    .where(Actor.name_supply_chain == session['name_supply_chain'])
    .where(Actor.generic_name == actor_reinitialized)
    ).scalars().all()
    if actor_to_change == None:
        erreur = 'Veuillez choisir un acteur à réinitialiser'
        flash(erreur)
        return render_template("supervise/create.html")
    
    for actor in actor_to_change:
        actor.firm_name = ''
        actor.password = ''
    db_session.commit()
    
    return redirect(url_for('supervise.lobby'))
        
@bp.route("/graphs", methods = ("GET",))
@login_required
@name_supply_chain_required
def graphs():
    name_supply_chain = session['name_supply_chain']
    # On récupère les rounds et on en fait une liste
    # Nombre de lignes dans la table Delivery_Command
    nber_lines_delivery_command=get_nber_lines_delivery_command(name_supply_chain) 
    # nber_lines_delivery_command = db_session.execute(
    # select(func.count(DeliveryCommand.name_client))
    # .select_from(DeliveryCommand)
    # .where(DeliveryCommand.name_supply_chain == name_supply_chain)
    # .where(DeliveryCommand.round>0)
    # ).scalars().first()

    # Nombre de relations clients_fournisseurs 
    nber_clients_suppliers=get_nber_clients_suppliers(name_supply_chain)
    # nber_clients_suppliers = db_session.execute(
    # select(func.count(ClientSupplier.name_client))
    # .select_from(ClientSupplier)
    # .where(ClientSupplier.name_supply_chain == name_supply_chain)
    # ).scalars().first()

    # On calcule le round actuel
    current_round = floor(nber_lines_delivery_command / (2*nber_clients_suppliers)) + 1

    # On crée une liste de rounds pour les absisses
    round_list = []
    for nber_round in range (current_round):
        round_list.append(nber_round+1)
    
    # Une fois que l'on a notre liste des rounds
    # Déterminons les restes à livrer à chaque round de chaque joueur

    # On récupère la liste des joueurs à partir de leur generic_name
    list_generic_name = db_session.execute(
    select(Actor.generic_name)
    .select_from(Actor)
    .where(Actor.name_supply_chain == name_supply_chain)
    .where(Actor.type == 'player')
    ).scalars().all()

    # Valeurs des pénalités
    penality_stock = 1 # En euros
    penality_rest_delivery = 2 

    # Liste des restes à livrer
    list_player_rest_penalty = []
    list_player_rest_penalty_cumulated = []

    # Liste des stocks
    list_player_stock_penalty = []
    list_player_stock_penalty_cumulated = []

    # Liste des stocks
    list_player_stock_and_rest_penalty = []
    list_player_stock_and_rest_penalty_cumulated = []
    # On crée une liste contenant pour chaque joueur, une liste avec 
    # On parcourt pour chaque joueur
    for name_actor in list_generic_name:
        # On initialise nos dictionnaires pour stocker 
        # les informations sur les restes à livrer de chaque joueur
        dict_rest = {}
        dict_rest_cumulated = {}
        dict_rest['name_actor'] = name_actor
        dict_rest_cumulated['name_actor'] = name_actor
        cumulated_rest = 0
        data_rest = []
        data_rest_cumulated = []
        # On initialise nos dictionnaires pour stocker 
        # les informations sur les stock de chaque joueur
        dict_stock = {}
        dict_stock_cumulated = {}
        dict_stock['name_actor'] = name_actor
        dict_stock_cumulated['name_actor'] = name_actor
        cumulated_stock = 0

        data_stock = []
        data_stock_cumulated = []

        # On initialise nos dictionnaires pour stocker 
        # les informations sur les stock et les restes de chaque joueur
        dict_stock_and_rest = {}
        dict_stock_and_rest_cumulated = {}
        dict_stock_and_rest['name_actor'] = name_actor
        dict_stock_and_rest_cumulated['name_actor'] = name_actor
        cumulated_stock_and_rest = 0

        data_stock_and_rest = []
        data_stock_and_rest_cumulated = []

        nber_round = len(round_list)
        # On parcourt pour chaque round
        for round in round_list:
            ### On s'occupe des restes à livrer d'abord

            # On fait la somme des commandes des clients du joueur
            sum_command_received = db_session.execute(
            select(func.coalesce(func.sum(func.coalesce(DeliveryCommand.quantity,0)),0).label('total_command'))
            .select_from(DeliveryCommand)
            .join(ClientSupplier)
            .where(and_(DeliveryCommand.name_supplier == name_actor, DeliveryCommand.name_supply_chain==name_supply_chain, DeliveryCommand.round<=round - ClientSupplier.command_time,DeliveryCommand.type=='command'))
            ).scalars().first()
        
            # On fait la somme de toutes les livraisons envoyées par le joueur
            sum_delivery_sent = db_session.execute(
            select(func.coalesce(func.sum(func.coalesce(DeliveryCommand.quantity,0)),0).label('total_delivery'))
            .select_from(DeliveryCommand)
            .where(and_(DeliveryCommand.name_supplier == name_actor, DeliveryCommand.name_supply_chain==name_supply_chain, DeliveryCommand.round<=round,DeliveryCommand.type=='delivery'))
            ).scalars().first()

            # On calcule les pénalités des restes à livrer 
            penality_rest = (sum_command_received - sum_delivery_sent) * penality_rest_delivery
            # Dictionnaire contenant le montant des pénalités à chaque round
            #dict_rest[f'{round}'] = penality_rest
            data_rest.append(penality_rest)
            # On ajoute la pénalité du round en plus des pénalités des rounds précédents
            cumulated_rest += (sum_command_received - sum_delivery_sent) * penality_rest_delivery
            
            # On l'ajoute ensuite dans notre dictionnaire des restes à livrer cumulé
            #dict_rest_cumulated[f'{round}'] = cumulated_rest
            data_rest_cumulated.append(cumulated_rest)
            ### On s'occupe des stocks ensuite
            
            # On calcule le stock client du joueur

            # On détermine le stock intial du joueur
            initial_stock = db_session.execute(
            select(Actor.initial_stock)
            .select_from(Actor)
            .where(and_(Actor.generic_name == name_actor, 
            Actor.name_supply_chain==name_supply_chain)
            )).scalars().first()
            
            # On détermine les livraisons que le joueur a reçu au round actuel
            # On fait la somme de toutes les livraisons reçues par le joueur
            sum_delivery_received = db_session.execute(
            select(func.coalesce(func.sum(func.coalesce(DeliveryCommand.quantity,0)),0).label('total_delivery'))
            .select_from(DeliveryCommand)
            .join(ClientSupplier)
            .where(and_(DeliveryCommand.name_client == name_actor, DeliveryCommand.name_supply_chain==name_supply_chain, DeliveryCommand.round<=round-ClientSupplier.delivery_time,DeliveryCommand.type=='delivery'))
            ).scalars().first()
            
            # On calcule le stock du round actuel
            round_stock = (initial_stock + sum_delivery_received - sum_delivery_sent) * penality_stock
            
            # On ajoute dans notre dictionnaire des pénalités des stocks
            #dict_stock[f'{round}'] = round_stock
            data_stock.append(round_stock)
            # On calcule le stock cumulé
            cumulated_stock += round_stock
            
            # On ajoute dans notre dictionnaire des pénalités des stocks en cumulés
            #dict_stock_cumulated[f'{round}'] = cumulated_stock
            data_stock_cumulated.append(cumulated_stock)

            # On calcule la somme des deux pénalités à chaque round pour le joueur

            round_total_penality = round_stock + penality_rest

            data_stock_and_rest.append(round_total_penality)
            cumulated_stock_and_rest+= round_total_penality

            data_stock_and_rest_cumulated.append(cumulated_stock_and_rest)

        random_red = randint(0,255)
        random_blue = randint(0,255)
        random_green = randint(0,255)

        color_line = f'rgb({random_red},{random_green},{random_blue})'
        
        # On ajoute la couleur dans nos dictionnaires
        dict_rest['border_color'] = color_line
        dict_rest_cumulated['border_color'] = color_line
        dict_stock['border_color'] = color_line
        dict_stock_cumulated['border_color'] = color_line
        dict_stock_and_rest['border_color'] = color_line
        dict_stock_and_rest_cumulated['border_color'] = color_line
        
        # On ajoute nos données
        dict_rest['data'] = data_rest
        dict_rest_cumulated['data'] = data_rest_cumulated
        dict_stock['data'] = data_stock
        dict_stock_cumulated['data'] = data_stock_cumulated
        dict_stock_and_rest['data'] = data_stock_and_rest
        dict_stock_and_rest_cumulated['data'] = data_stock_and_rest_cumulated
        
        # On ajoute ainsi à chaque boucle le dictionnaire d'un joueur pour tous les rounds
        # Le dictionnaire des pénalités de restes à livrer à chaque round
        list_player_rest_penalty.append(dict_rest)
        
        # Le dictionnaire des pénalités de restes à livrer en cumulé à chaque round
        list_player_rest_penalty_cumulated.append(dict_rest_cumulated)

        # Le dictionnaire des pénalités de restes à livrer à chaque round
        list_player_stock_penalty.append(dict_stock)
        
        # Le dictionnaire des pénalités de restes à livrer en cumulé à chaque round
        list_player_stock_penalty_cumulated.append(dict_stock_cumulated)

        # Le dictionnaire des pénalités de restes à livrer et des stocks à chaque round
        list_player_stock_and_rest_penalty.append(dict_stock_and_rest)

        # Le dictionnaire des pénalités de restes à livrer et des stocks en cumulé à chaque round
        list_player_stock_and_rest_penalty_cumulated.append(dict_stock_and_rest_cumulated)

    #flash(list_player_rest_penalty)
    #return render_template('play/waiting_room.html')
    # # Dès qu'on a fini de créer nos dictionnaires pour chaque joueur et round
    # # On va les utiliser pour la page des graphiques

    return render_template("supervise/graphics.html", list_player_rest_penalty = list_player_rest_penalty , list_player_rest_penalty_cumulated = list_player_rest_penalty_cumulated, 
    list_player_stock_penalty = list_player_stock_penalty , 
    list_player_stock_penalty_cumulated = list_player_stock_penalty_cumulated, 
    round_list = round_list, nber_round =nber_round, 
    list_player_stock_and_rest_penalty = list_player_stock_and_rest_penalty, 
    list_player_stock_and_rest_penalty_cumulated =  list_player_stock_and_rest_penalty_cumulated)

            # # On fait la somme de toutes les livraisons pour chaque client du joueur
            # sum_delivery_clients = db_session.execute(
            # select(DeliveryCommand.name_client, func.coalesce(func.sum(DeliveryCommand.quantity),0).label('total_delivery'))
            # .select_from(DeliveryCommand)
            # .where(and_(DeliveryCommand.name_supplier == name_actor, DeliveryCommand.name_supply_chain==name_supply_chain, DeliveryCommand.round<=round,DeliveryCommand.type=='delivery'))
            # .group_by(DeliveryCommand.name_client)
            # ).all()

            # # On fait la somme de toutes les commandes pour chaque client du joueur
            # sum_command_clients = db_session.execute(
            # select(DeliveryCommand.name_client, func.coalesce(func.sum(DeliveryCommand.quantity),0).label('total_command'))
            # .select_from(DeliveryCommand)
            # .where(and_(DeliveryCommand.name_supplier == name_actor, DeliveryCommand.name_supply_chain==name_supply_chain, DeliveryCommand.round<=round - DeliveryCommand.command_time,DeliveryCommand.type=='command'))
            # .group_by(DeliveryCommand.name_client)
            # ).all()

            # for client in sum_command_clients:
            #     dict = {"name_client" : client["name_client"],  "quantity": client["total_command"]}
            #     rest_command.append(dict)
            #     #rest_command.add(client["name_client"],client["total_command"])
            
            # for client in sum_delivery_clients:
            #     dict = {"name_client" : client["name_client"],  "quantity": client["total_delivery"]}
            #     rest_delivery.append(dict)
            # # On calcule les restes à livrer
            # for command_passed in range (len(rest_command)):
            #     name_client = rest_command[command_passed]["name_client"]
            #     #
            #     for command_delivered in range (len(rest_delivery)):
            #         # dict = {"name_client": name_client, "quantity" : rest_command[command_passed]["quantity"] - rest_delivery[command_delivered]["quantity"]}
            #         if name_client == rest_delivery[command_delivered]["name_client"]:
            #             dict = {"name_client": name_client, "quantity" : rest_command[command_passed]["quantity"] - rest_delivery[command_delivered]["quantity"]}
            #             rest_total.append(dict)
            #             break

@bp.route("/state_game",methods=("GET",))
@login_required
@name_supply_chain_required
def state_game():
    name_supply_chain=session['name_supply_chain']
    state_game=db_session.execute(
        select(SupplyChain)
        .select_from(SupplyChain)
        .where(SupplyChain.name==name_supply_chain)
    ).scalars().all()

    for state in state_game:
        if state.end_game == False:
            state.end_game=True
        else :
            state.end_game=False
        
    db_session.commit()

    return redirect(url_for('supervise.dashboard'))
