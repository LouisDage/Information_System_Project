from math import floor

from flask import session, request
from sqlalchemy import select, and_, func

from beergame.function_util import get_client_deliveries, get_etape
from beergame.db import db_session, SupplyChain, Actor, ClientSupplier, DeliveryCommand


def get_all_players_from_one_supply_chain(name_supply_chain):
    """
    Function that returns all players from one supply chain.
    """
    actors = db_session.execute(
        select(Actor.generic_name, Actor.firm_name, Actor.initial_stock)
        .where(and_(
            Actor.name_supply_chain==name_supply_chain,
            Actor.type=="player",
        ))
        .order_by(Actor.generic_name)
    )
    return actors

def create_new_supply_chain(name_supply_chain):
    """
    Method that create a new supply chain in the DB.
    """
    new_supply_chain = SupplyChain(
        name=name_supply_chain,
        total_round_number=5,
        penality_stock=2,
        penality_late=1,
        id_supervisor=session["user_id"],
        end_game= False,
    )
    db_session.add(new_supply_chain)

def create_all_actors_for_a_supply_chain(name_supply_chain):
    """
    Method that create all actors for a new supply chain in the DB.
    """
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
    for actor_name in actor_names:
        # Creates every actor of the supply chain
        actor_type="player"
        if actor_name == "Infinite Supplier":
            actor_type="universal_supplier"
        elif "Client" in actor_name:
            actor_type="universal_client"
        new_actor=Actor(
            generic_name=actor_name,
            firm_name="",
            initial_stock=500,
            password="",
            type=actor_type,
            name_supply_chain=name_supply_chain,
        )
        db_session.add(new_actor)

def create_relationship_between_actors(name_supply_chain):
    """
    Method that initialize the relationship between all
    actors of a new supply chain in the DB.
    """
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
    for relation in relation_between_actors:
        new_relation=ClientSupplier(
            name_supply_chain=name_supply_chain,
            name_client=relation["client"],
            name_supplier=relation["supplier"],
            command_time=1,
            delivery_time=1,
        )
        db_session.add(new_relation)
        create_initial_command(new_relation)


def create_initial_command(relation_between_two_actor):
    """
    Method to create the initial command of a relation between two actors
    of a new supply chain in the DB.
    """
    new_delivery=DeliveryCommand(
        name_client=relation_between_two_actor.name_client,
        name_supply_chain=relation_between_two_actor.name_supply_chain,
        name_supplier=relation_between_two_actor.name_supplier,
        type="delivery",
        round=0,
        quantity=50,
        seen_by_actor=False,
    )
    db_session.add(new_delivery)
    for number_round in [0,1]:
        new_command=DeliveryCommand(
            name_client=relation_between_two_actor.name_client,
            name_supply_chain=relation_between_two_actor.name_supply_chain,
            name_supplier=relation_between_two_actor.name_supplier,
            type="command",
            round=number_round-1,
            quantity=50,
            seen_by_actor=False,
        )
        db_session.add(new_command)

def to_int(string):
    if string == '':
        return None
    return int(string)

def get_tracking_sheet_data(generic_name):
    name_supply_chain = session['name_supply_chain']

    # if session["actor_generic_name"]:
    #     generic_name = session["actor_generic_name"]
    # else:
    #     generic_name = request.form.get("actor_name", '').strip()
    # On récupère les rounds et on en fait une liste
    # Nombre de lignes dans la table Delivery_Command 
    # On récupère les rounds et on en fait une liste
    # Nombre de lignes dans la table Delivery_Command 
    nber_lines_delivery_command = db_session.execute(
    select(func.count(DeliveryCommand.name_client))
    .select_from(DeliveryCommand)
    .where(DeliveryCommand.name_supply_chain == name_supply_chain)
    .where(DeliveryCommand.round>0)
    ).scalars().first()

    # Nombre de relations clients_fournisseurs 
    nber_clients_suppliers = db_session.execute(
    select(func.count(ClientSupplier.name_client))
    .select_from(ClientSupplier)
    .where(ClientSupplier.name_supply_chain == name_supply_chain)
    ).scalars().first()

    # On calcule le round actuel
    current_round = floor(nber_lines_delivery_command / (2*nber_clients_suppliers)) + 1

    # On crée une liste de rounds pour les absisses
    round_list = []
    data=[]
    for nber_round in range (current_round):
        round_list.append(nber_round+1)
        # On fait une disjonction de cas sur les rounds inférieurs au round actuel
 
    # On détermine le numéro de l'étape

    # On récupère les livraisons du joueur pour l'étape 4
    client_deliveries=get_client_deliveries(name_supply_chain,current_round,generic_name)
    # client_deliveries = db_session.execute(
    # select(DeliveryCommand.name_supplier, DeliveryCommand.quantity, DeliveryCommand.seen_by_actor)
    # .select_from(DeliveryCommand)
    # .join(ClientSupplier, and_(ClientSupplier.name_client == DeliveryCommand.name_client, 
    # ClientSupplier.name_supply_chain == DeliveryCommand.name_supply_chain, 
    # ClientSupplier.name_supplier == DeliveryCommand.name_supplier ))
    # .where(and_(DeliveryCommand.name_client == generic_name, 
    # DeliveryCommand.name_supply_chain==name_supply_chain, 
    # DeliveryCommand.round==current_round - ClientSupplier.delivery_time,
    # DeliveryCommand.type=='delivery',DeliveryCommand.round>0))
    # ).all()
    
    # On récupère les demandes clients du joueur
    client_demands = db_session.execute(
    select(DeliveryCommand.name_client, DeliveryCommand.quantity, DeliveryCommand.seen_by_actor)
    .select_from(DeliveryCommand)
    .join(ClientSupplier, and_(ClientSupplier.name_client == DeliveryCommand.name_client, 
    ClientSupplier.name_supply_chain == DeliveryCommand.name_supply_chain, 
    ClientSupplier.name_supplier == DeliveryCommand.name_supplier ))
    .where(and_(DeliveryCommand.name_supplier == generic_name, 
    DeliveryCommand.name_supply_chain==name_supply_chain, 
    DeliveryCommand.round== current_round - ClientSupplier.command_time, #ça fonctionne car command_time=1
    DeliveryCommand.type=='command',
    ))
    ).all()

    
    if nber_lines_delivery_command % (2 * nber_clients_suppliers) == 0 and client_demands[0]['seen_by_actor'] == False:
        etape = 1
    elif nber_lines_delivery_command % (2 * nber_clients_suppliers) >= nber_clients_suppliers and client_deliveries[0]['seen_by_actor'] == True:
        etape = 4
    # On est à l'étape 1
    #etape=4
        # On récupère la demande des clients du joueur
    etape=get_etape(nber_lines_delivery_command,nber_clients_suppliers,client_demands,client_deliveries)
    for round in round_list:
        
        if round < current_round:
            round_line = {}
            # On récupère le round
            round_line['round'] = round
            # On récupère les demandes clients du joueur
            # ça fonctionne
            client_demands = db_session.execute(
            select(ClientSupplier.name_client, func.coalesce(DeliveryCommand.quantity,0).label('quantity'))
            .select_from(DeliveryCommand)
            .join(ClientSupplier, and_(ClientSupplier.name_client == DeliveryCommand.name_client, 
            ClientSupplier.name_supply_chain == DeliveryCommand.name_supply_chain, 
            ClientSupplier.name_supplier == DeliveryCommand.name_supplier ))
            .where(and_(DeliveryCommand.name_supplier == generic_name, 
            DeliveryCommand.name_supply_chain==name_supply_chain, 
            DeliveryCommand.round== round - ClientSupplier.command_time, #ça fonctionne car command_time=1
            DeliveryCommand.type=='command'))
            ).all()
            round_line['client_demands'] = client_demands

            # On récupère les livraisons que va envoyer le joueur
            # ça fonctionne
            player_deliveries = db_session.execute(
            select(DeliveryCommand.name_client, func.coalesce(DeliveryCommand.quantity,0).label('quantity'))
            .select_from(DeliveryCommand)
            .join(ClientSupplier, and_(ClientSupplier.name_client == DeliveryCommand.name_client, 
            ClientSupplier.name_supply_chain == DeliveryCommand.name_supply_chain, 
            ClientSupplier.name_supplier == DeliveryCommand.name_supplier ))
            .where(and_(DeliveryCommand.name_supplier == generic_name, 
            DeliveryCommand.name_supply_chain==name_supply_chain, 
            DeliveryCommand.round==round,
            DeliveryCommand.type=='delivery'))
            ).all()
            
            round_line['client_deliveries'] = player_deliveries
            # On récupère les restes à livrer du joueur

            # On fait la somme des commandes des clients du joueur
            sum_command_received = db_session.execute(
            select(DeliveryCommand.name_client,func.coalesce(func.sum(func.coalesce(DeliveryCommand.quantity,0)),0).label('total_command'))
            .select_from(DeliveryCommand)
            .join(ClientSupplier)
            .where(and_(DeliveryCommand.name_supplier == generic_name, 
            DeliveryCommand.name_supply_chain==name_supply_chain, 
            DeliveryCommand.round<=round - ClientSupplier.command_time,
            DeliveryCommand.type=='command'))
            .group_by(DeliveryCommand.name_client)
            ).all()
        
            # On fait la somme de toutes les livraisons envoyées par le joueur
            sum_delivery_sent = db_session.execute(
            select(DeliveryCommand.name_client,func.coalesce(func.sum(func.coalesce(DeliveryCommand.quantity,0)),0).label('total_delivery'))
            .select_from(DeliveryCommand)
            .where(and_(DeliveryCommand.name_supplier == generic_name, DeliveryCommand.name_supply_chain==name_supply_chain, 
            DeliveryCommand.round<=round,DeliveryCommand.type=='delivery'))
            .group_by(DeliveryCommand.name_client)
            ).all()
            
            nber_client = db_session.execute(
            select(func.count(ClientSupplier.name_client))
            .select_from(ClientSupplier)
            .where(and_(ClientSupplier.name_supplier == generic_name, ClientSupplier.name_supply_chain==name_supply_chain)
            )).scalars().first()
            
            # On récupère les restes à livrer des clients du joueur
            # ça fonctionne
            list_rest = []
            for client in range (nber_client):
               list_rest.append({'name_client': sum_command_received[client]['name_client'], 'total_rest': sum_command_received[client]['total_command'] - sum_delivery_sent[client]['total_delivery']})
            
            round_line['rest_delivery'] = list_rest
            
            # On récupère les livraisons reçues par le joueur

            # On détermine le stock intial du joueur
            initial_stock = db_session.execute(
            select(Actor.initial_stock)
            .select_from(Actor)
            .where(and_(Actor.generic_name == generic_name, 
            Actor.name_supply_chain==name_supply_chain)
            )).scalars().first()
            
            # Réception
            # ça fonctionne
            # On détermine les livraisons que le joueur a reçu au round actuel
            # On fait la somme de toutes les livraisons reçues par le joueur
            delivery_received = db_session.execute(
            select(DeliveryCommand.name_supplier,func.coalesce(DeliveryCommand.quantity,0).label('total_delivery'))
            .select_from(DeliveryCommand)
            .join(ClientSupplier)
            .where(and_(DeliveryCommand.name_client == generic_name, 
            DeliveryCommand.name_supply_chain==name_supply_chain, 
            DeliveryCommand.round == round-ClientSupplier.delivery_time,
            DeliveryCommand.type=='delivery'))
            ).all()


            sum_delivery_received = db_session.execute(
            select(func.sum(func.coalesce(DeliveryCommand.quantity,0)).label('total_delivery'))
            .select_from(DeliveryCommand)
            .join(ClientSupplier)
            .where(and_(DeliveryCommand.name_client == generic_name, 
            DeliveryCommand.name_supply_chain==name_supply_chain, 
            DeliveryCommand.round <= round-ClientSupplier.delivery_time,
            DeliveryCommand.type=='delivery'))
            ).scalars().first()
            
            round_line['reception'] = delivery_received

            # On fait la somme de toutes les livraisons envoyées par le joueur
            sum_delivery_sent_all_players = db_session.execute(
            select(func.coalesce(func.sum(func.coalesce(DeliveryCommand.quantity,0)),0).label('total_delivery'))
            .select_from(DeliveryCommand)
            .where(and_(DeliveryCommand.name_supplier == generic_name, 
            DeliveryCommand.name_supply_chain==name_supply_chain, 
            DeliveryCommand.round<=round,
            DeliveryCommand.type=='delivery'))
            .group_by(DeliveryCommand.name_client)
            ).scalars().first()

            # On calcule le stock du round actuel,# On récupèrè la valeur du stock
            # ça fonctionne
            round_stock = (initial_stock + sum_delivery_received - sum_delivery_sent_all_players) 
            round_line['round_stock'] = round_stock

            # On récupère demandes envoyées par le joueur 
            player_demands = db_session.execute(
            select(DeliveryCommand.name_client, func.coalesce(DeliveryCommand.quantity,0).label('quantity'), DeliveryCommand.seen_by_actor)
            .select_from(DeliveryCommand)
            .join(ClientSupplier, and_(ClientSupplier.name_client == DeliveryCommand.name_client, 
            ClientSupplier.name_supply_chain == DeliveryCommand.name_supply_chain, 
            ClientSupplier.name_supplier == DeliveryCommand.name_supplier ))
            .where(and_(DeliveryCommand.name_client == generic_name, 
            DeliveryCommand.name_supply_chain==name_supply_chain, 
            DeliveryCommand.round== round, #ça fonctionne car command_time=1
            DeliveryCommand.type=='command'))
            ).all()

            round_line['player_demands'] = player_demands

            data.append(round_line)
        
        elif round == current_round:
            # Si on est à l'étape 1 on ne passe jamais ici
            current_round_line = {}
            current_round_line['round'] = round
            if etape >= 2:
                # On récupère les demandes clients du joueur
                client_demands = db_session.execute(
                select(DeliveryCommand.name_client, func.coalesce(DeliveryCommand.quantity,0).label('quantity'), DeliveryCommand.seen_by_actor)
                .select_from(DeliveryCommand)
                .join(ClientSupplier, and_(ClientSupplier.name_client == DeliveryCommand.name_client, 
                ClientSupplier.name_supply_chain == DeliveryCommand.name_supply_chain, 
                ClientSupplier.name_supplier == DeliveryCommand.name_supplier ))
                .where(and_(DeliveryCommand.name_supplier == generic_name, 
                DeliveryCommand.name_supply_chain==name_supply_chain, 
                DeliveryCommand.round== round - ClientSupplier.command_time, #ça fonctionne car command_time=1
                DeliveryCommand.type=='command'))
                ).all()
                current_round_line['client_demands'] = client_demands
        
            if etape >=3:
                # On récupère les livraisons que va envoyer le joueur
                player_deliveries = db_session.execute(
                select(DeliveryCommand.name_client, func.coalesce(DeliveryCommand.quantity,0).label('quantity'))
                .select_from(DeliveryCommand)
                .join(ClientSupplier, and_(ClientSupplier.name_client == DeliveryCommand.name_client, 
                ClientSupplier.name_supply_chain == DeliveryCommand.name_supply_chain, 
                ClientSupplier.name_supplier == DeliveryCommand.name_supplier ))
                .where(and_(DeliveryCommand.name_supplier == generic_name, 
                DeliveryCommand.name_supply_chain==name_supply_chain, 
                DeliveryCommand.round==round,
                DeliveryCommand.type=='delivery'))
                ).all()

                current_round_line['client_deliveries'] = player_deliveries

                # Restes à livrer

                # On calcule la somme des commandes des rounds de chaque client du joueur

                sum_command_received = db_session.execute(
                select(DeliveryCommand.name_client,func.coalesce(func.sum(func.coalesce(DeliveryCommand.quantity,0)),0).label('total_command'))
                .select_from(DeliveryCommand)
                .join(ClientSupplier)
                .where(and_(DeliveryCommand.name_supplier == generic_name, 
                DeliveryCommand.name_supply_chain==name_supply_chain, 
                DeliveryCommand.round<=round - ClientSupplier.command_time,
                DeliveryCommand.type=='command'))
                .group_by(DeliveryCommand.name_client)
                ).all()
               
                # On calcule la somme des livraisons des rounds de chaque client du joueur
                sum_delivery_sent = db_session.execute(
                select(DeliveryCommand.name_client,func.coalesce(func.sum(func.coalesce(DeliveryCommand.quantity,0)),0).label('total_delivery'))
                .select_from(DeliveryCommand)
                .where(and_(DeliveryCommand.name_supplier == generic_name, DeliveryCommand.name_supply_chain==name_supply_chain, 
                DeliveryCommand.round<=round,DeliveryCommand.type=='delivery'))
                .group_by(DeliveryCommand.name_client)
                ).all()
                
                # On détermine le nombre de client
                nber_client = db_session.execute(
                select(func.count(ClientSupplier.name_client))
                .select_from(ClientSupplier)
                .where(and_(ClientSupplier.name_supplier == generic_name, ClientSupplier.name_supply_chain==name_supply_chain)
                )).scalars().first()
                
                # On crée une liste des restes à livrer pour chaque joueur
                list_rest = []
                for client in range (nber_client):
                    list_rest.append({'name_client': sum_command_received[client]['name_client'], 'total_rest': sum_command_received[client]['total_command'] - sum_delivery_sent[client]['total_delivery']})

                current_round_line['rest_delivery'] = list_rest
                
            if etape >= 4:
                # On récupère les livraisons reçues par le joueur
                # Il faut vérifier ici

                # On détermine le stock intial du joueur
                initial_stock = db_session.execute(
                select(Actor.initial_stock)
                .select_from(Actor)
                .where(and_(Actor.generic_name == generic_name, 
                Actor.name_supply_chain==name_supply_chain)
                )).scalars().first()
                

                # Réception
                # ça fonctionne
                # On détermine les livraisons que le joueur a reçu au round actuel
                # On fait la somme de toutes les livraisons reçues par le joueur
                delivery_received = db_session.execute(
                select(DeliveryCommand.name_supplier,func.coalesce(DeliveryCommand.quantity,0).label('total_delivery'))
                .select_from(DeliveryCommand)
                .join(ClientSupplier)
                .where(and_(DeliveryCommand.name_client == generic_name, 
                DeliveryCommand.name_supply_chain==name_supply_chain, 
                DeliveryCommand.round == round-ClientSupplier.delivery_time,
                DeliveryCommand.type=='delivery'))
                ).all()


                sum_delivery_received = db_session.execute(
                select(func.coalesce(func.sum(func.coalesce(DeliveryCommand.quantity,0)),0).label('total_delivery'))
                .select_from(DeliveryCommand)
                .join(ClientSupplier)
                .where(and_(DeliveryCommand.name_client == generic_name, 
                DeliveryCommand.name_supply_chain==name_supply_chain, 
                DeliveryCommand.round <= round-ClientSupplier.delivery_time,
                DeliveryCommand.type=='delivery'))
                ).scalars().first()
                
                current_round_line['reception'] = delivery_received

                # On fait la somme de toutes les livraisons envoyées par le joueur
                sum_delivery_sent_all_players = db_session.execute(
                select(func.coalesce(func.sum(func.coalesce(DeliveryCommand.quantity,0)),0).label('total_delivery'))
                .select_from(DeliveryCommand)
                .where(and_(DeliveryCommand.name_supplier == generic_name, 
                DeliveryCommand.name_supply_chain==name_supply_chain, 
                DeliveryCommand.round<=round,
                DeliveryCommand.type=='delivery'))
                .group_by(DeliveryCommand.name_client)
                ).scalars().first()
                # On calcule le stock du round actuel,# On récupèrè la valeur du stock
                # ça fonctionne
                round_stock = (initial_stock + sum_delivery_received - sum_delivery_sent_all_players) 
            
                current_round_line['round_stock'] = round_stock

            data.append(current_round_line)
    return data
