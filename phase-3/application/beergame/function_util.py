from math import floor

from sqlalchemy import select, func, and_

from beergame.db import DeliveryCommand, db_session, Actor,ClientSupplier


def get_etape(nber_lines_delivery_command,nber_clients_suppliers_interactions,client_demands,client_deliveries):
    if nber_lines_delivery_command % (2*nber_clients_suppliers_interactions) < nber_clients_suppliers_interactions and client_demands[0]['seen_by_actor'] == False:
        etape=1
    if nber_lines_delivery_command % (2*nber_clients_suppliers_interactions) < nber_clients_suppliers_interactions and client_demands[0]['seen_by_actor'] == True:
        etape=2
    elif nber_lines_delivery_command % (2*nber_clients_suppliers_interactions)>=nber_clients_suppliers_interactions and client_deliveries[0]['seen_by_actor'] == False:
        etape=3
    elif nber_lines_delivery_command % (2*nber_clients_suppliers_interactions) >= nber_clients_suppliers_interactions and client_deliveries[0]['seen_by_actor'] == True:
        etape=4
    return etape


# Commandes passées au joueur (par ses clients)
def get_client_demands(name_supply_chain,current_round,generic_name):
    client_demands = db_session.execute(
    select(DeliveryCommand.name_client,  func.coalesce(DeliveryCommand.quantity,0).label('quantity'), DeliveryCommand.seen_by_actor)
    .select_from(DeliveryCommand)
    .join(ClientSupplier, and_(ClientSupplier.name_client == DeliveryCommand.name_client, 
    ClientSupplier.name_supply_chain == DeliveryCommand.name_supply_chain, 
    ClientSupplier.name_supplier == DeliveryCommand.name_supplier ))
    .where(and_(DeliveryCommand.name_supplier == generic_name, 
    DeliveryCommand.name_supply_chain==name_supply_chain, 
    DeliveryCommand.round==current_round - ClientSupplier.command_time, #ça fonctionne car command_time=1
    DeliveryCommand.type=='command'))
    ).all()
    return client_demands

#Commande passés par le joueur
def get_player_demands(name_supply_chain,current_round,generic_name):
    player_demands = db_session.execute(
    select(DeliveryCommand.name_client, DeliveryCommand.quantity, DeliveryCommand.seen_by_actor)
    .select_from(DeliveryCommand)
    .join(ClientSupplier, and_(ClientSupplier.name_client == DeliveryCommand.name_client, 
    ClientSupplier.name_supply_chain == DeliveryCommand.name_supply_chain, 
    ClientSupplier.name_supplier == DeliveryCommand.name_supplier ))
    .where(and_(DeliveryCommand.name_client == generic_name, 
    DeliveryCommand.name_supply_chain==name_supply_chain, 
    DeliveryCommand.round==current_round - ClientSupplier.command_time, #ça fonctionne car command_time=1
    DeliveryCommand.type=='command'))
    ).all()
    return player_demands

# On récupère les livraisons reçues par le joueur 
def get_client_deliveries(name_supply_chain,current_round,generic_name):
    client_deliveries = db_session.execute(
    select(DeliveryCommand.name_supplier,  func.coalesce(DeliveryCommand.quantity,0).label('quantity'), DeliveryCommand.seen_by_actor)
    .select_from(DeliveryCommand)
    .join(ClientSupplier, and_(ClientSupplier.name_client == DeliveryCommand.name_client, 
    ClientSupplier.name_supply_chain == DeliveryCommand.name_supply_chain, 
    ClientSupplier.name_supplier == DeliveryCommand.name_supplier ))
    .where(and_(DeliveryCommand.name_client == generic_name, 
    DeliveryCommand.name_supply_chain==name_supply_chain, 
    DeliveryCommand.round==current_round - ClientSupplier.delivery_time,
    DeliveryCommand.type=='delivery'))
    ).all()
    return client_deliveries

#Livraisons envoyés par le joueur 
def get_player_deliveries(name_supply_chain,current_round,generic_name):
    player_deliveries = db_session.execute(
    select(DeliveryCommand.name_supplier, DeliveryCommand.quantity, DeliveryCommand.seen_by_actor)
    .select_from(DeliveryCommand)
    .join(ClientSupplier, and_(ClientSupplier.name_client == DeliveryCommand.name_client, 
    ClientSupplier.name_supply_chain == DeliveryCommand.name_supply_chain, 
    ClientSupplier.name_supplier == DeliveryCommand.name_supplier ))
    .where(and_(DeliveryCommand.name_supplier == generic_name, 
    DeliveryCommand.name_supply_chain==name_supply_chain, 
    DeliveryCommand.round==current_round - ClientSupplier.delivery_time,
    DeliveryCommand.type=='delivery'))
    ).all()
    return player_deliveries

# Round actuel
def get_current_round(nber_lines_delivery_command,nber_clients_suppliers):
    current_round = floor(nber_lines_delivery_command / (2*nber_clients_suppliers)) + 1
    return current_round


# Nombre de lignes dans la table Delivery_Command 
def get_nber_lines_delivery_command(name_supply_chain):
    nber_lines_delivery_command = db_session.execute(
    select(func.count(DeliveryCommand.name_client))
    .select_from(DeliveryCommand)
    .where(DeliveryCommand.name_supply_chain == name_supply_chain)
    .where(DeliveryCommand.round>0)
    ).scalars().first()
    return nber_lines_delivery_command

# Nombre de relations clients_fournisseurs
def get_nber_clients_suppliers(name_supply_chain):
    nber_clients_suppliers = db_session.execute(
    select(func.count(ClientSupplier.name_client))
    .select_from(ClientSupplier)
    .where(ClientSupplier.name_supply_chain == name_supply_chain)
    ).scalars().first()
    return nber_clients_suppliers

# Nombre de fournisseur du joueur
def get_nber_suppliers_player(name_supply_chain,generic_name):
    nber_suppliers_player = db_session.execute(
    select(func.count(ClientSupplier.name_supplier))
    .select_from(ClientSupplier)
    .where(and_(ClientSupplier.name_client == generic_name, 
    ClientSupplier.name_supply_chain == name_supply_chain))
    ).scalars().first()
    return nber_suppliers_player


#nombre de clients du joueur:
def get_nber_clients_player(name_supply_chain,generic_name):
    nber_clients_player = db_session.execute(
    select(func.count(ClientSupplier.name_supplier))
    .select_from(ClientSupplier)
    .where(and_(ClientSupplier.name_supplier == generic_name, 
    ClientSupplier.name_supply_chain == name_supply_chain))
    ).scalars().first()
    return nber_clients_player


# On récupère les demandes du joueur
def player_demands_find(name_supply_chain,player_name,current_round):
    player_demands = db_session.execute(
    select(DeliveryCommand.name_supplier, func.coalesce(DeliveryCommand.quantity,0).label('quantity'), DeliveryCommand.seen_by_actor)
    .select_from(DeliveryCommand)
    .join(ClientSupplier, and_(ClientSupplier.name_client == DeliveryCommand.name_client, 
    ClientSupplier.name_supply_chain == DeliveryCommand.name_supply_chain, 
    ClientSupplier.name_supplier == DeliveryCommand.name_supplier ))
    .where(and_(DeliveryCommand.name_client == player_name, 
    DeliveryCommand.name_supply_chain==name_supply_chain, 
    DeliveryCommand.round==current_round - ClientSupplier.command_time, #ça fonctionne car command_time=1
    DeliveryCommand.type=='command')) # Au lieu de delivery
    ).all()
    return player_demands

def get_number_taken_actors(current_round,etape, name_supply_chain):
    nber_player_ready = 0
    if etape == 2:
        # On récupère les joueurs qui ont déjà envoyés leurs livraisons
        list_players = db_session.execute(
            select(Actor.generic_name)
            .select_from(Actor)
            .where(and_(Actor.name_supply_chain==name_supply_chain))
            ).all()
        
        for player in list_players:
            delivery_current_round = db_session.execute(
            select(DeliveryCommand.name_client, func.coalesce(DeliveryCommand.quantity,0), DeliveryCommand.seen_by_actor)
            .select_from(DeliveryCommand)
            .join(ClientSupplier, and_(ClientSupplier.name_client == DeliveryCommand.name_client, 
            ClientSupplier.name_supply_chain == DeliveryCommand.name_supply_chain, 
            ClientSupplier.name_supplier == DeliveryCommand.name_supplier ))
            .where(and_(DeliveryCommand.name_supplier == player['generic_name'], 
            DeliveryCommand.name_supply_chain==name_supply_chain, 
            DeliveryCommand.round==current_round, #ça fonctionne car command_time=1
            DeliveryCommand.type=='delivery')) # Au lieu de delivery
            ).scalars().first()
            if delivery_current_round != None :
                nber_player_ready += 1
        
    elif etape == 4 :
        # On récupère les joueurs qui ont déjà envoyés leurs commandes
        list_players = db_session.execute(
            select(Actor.generic_name)
            .select_from(Actor)
            .where(and_(Actor.name_supply_chain==name_supply_chain))
            ).all()
        
        for player in list_players:
            delivery_current_round = db_session.execute(
            select(DeliveryCommand.name_client, func.coalesce(DeliveryCommand.quantity,0), DeliveryCommand.seen_by_actor)
            .select_from(DeliveryCommand)
            .join(ClientSupplier, and_(ClientSupplier.name_client == DeliveryCommand.name_client, 
            ClientSupplier.name_supply_chain == DeliveryCommand.name_supply_chain, 
            ClientSupplier.name_supplier == DeliveryCommand.name_supplier ))
            .where(and_(DeliveryCommand.name_client == player['generic_name'], 
            DeliveryCommand.name_supply_chain==name_supply_chain, 
            DeliveryCommand.round==current_round, #ça fonctionne car command_time=1
            DeliveryCommand.type=='command')) # Au lieu de delivery
            ).scalars().first()
            if delivery_current_round != None :
                nber_player_ready += 1

    return nber_player_ready
 
#Nombre de lignes de types livraisons au current_round
def get_nber_delivery_exist(name_supply_chain,current_round,name_player):
    nber_delivery_exist=db_session.execute(
        select(func.count(DeliveryCommand.name_client))
        .select_from(DeliveryCommand)
        .where(and_(DeliveryCommand.name_supply_chain == name_supply_chain, 
        DeliveryCommand.name_supplier == name_player, 
        DeliveryCommand.type=='delivery', 
        DeliveryCommand.round ==current_round,
        DeliveryCommand.seen_by_actor=='False'))
        ).scalars().first()
    return nber_delivery_exist

#Nombre de lignes de types commande au current_round
def get_nber_command_exist(name_supply_chain,current_round,name_player):
    nber_command_exist=db_session.execute(
        select(func.count(DeliveryCommand.name_client))
        .select_from(DeliveryCommand)
        .where(and_(DeliveryCommand.name_supply_chain == name_supply_chain, 
        DeliveryCommand.name_client == name_player, 
        DeliveryCommand.type=='command', 
        DeliveryCommand.round ==current_round,
        DeliveryCommand.seen_by_actor=='False'))
        ).scalars().first()
    return nber_command_exist

#somme des livraisons effectuées à un round donné 
def get_sum_delivery_sent(name_supply_chain,round,generic_name):
    sum_delivery_sent = db_session.execute(
        select(DeliveryCommand.name_client,
        func.coalesce(func.sum(func.coalesce(DeliveryCommand.quantity,0)),0).label('total_delivery'))
        .select_from(DeliveryCommand)
        .where(and_(DeliveryCommand.name_supplier == generic_name, 
        DeliveryCommand.name_supply_chain==name_supply_chain, 
        DeliveryCommand.round<=round,DeliveryCommand.type=='delivery'))
        .group_by(DeliveryCommand.name_client)
        ).all()
    return sum_delivery_sent


def get_sum_command_reiceved(name_supply_chain,round,generic_name):
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
    return sum_command_received

def get_sum_delivery_received(name_supply_chain,round,generic_name):
    sum_delivery_received = db_session.execute(
        select(DeliveryCommand.name_supplier,
        func.coalesce(DeliveryCommand.quantity,0).label('total_delivery'))
        .select_from(DeliveryCommand)
        .join(ClientSupplier)
        .where(and_(DeliveryCommand.name_client == generic_name, 
        DeliveryCommand.name_supply_chain==name_supply_chain, 
        DeliveryCommand.round == round-ClientSupplier.delivery_time,
        DeliveryCommand.type=='delivery'))
        ).all()
    return sum_delivery_received


