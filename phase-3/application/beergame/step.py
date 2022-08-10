# Tous ces logins
from math import *

from flask import (
  flash, g, redirect, render_template, request, url_for, session,
)

from sqlalchemy import select, func, and_
from beergame.db import DeliveryCommand, SupplyChain, db_session, Actor,ClientSupplier
from beergame.utils import get_tracking_sheet_data
from beergame.function_util import (
    get_number_taken_actors,
)

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

def get_step_1(client_demands,etape,current_round, generic_name,name_supply_chain):
     # Pour l'étape 1 si toutes les commandes des joueurs ont été envoyées
     if etape==1:
        state_game = db_session.execute( # Pour changer l'état du bouton, True si la partie est finie
        select(SupplyChain.end_game)
        .select_from(SupplyChain)
        .where(and_(SupplyChain.name == name_supply_chain))
        ).scalars().first()
        running_commands = player_demands_not_sent(generic_name,name_supply_chain,current_round, etape)
        current_round_stock = current_round_stock_find(current_round,generic_name,name_supply_chain,etape)
        tracking_sheet_data = get_tracking_sheet_data(generic_name)
        return render_template('play/dashboard.html', 
                               data=tracking_sheet_data,
                               etape=etape, 
                               client_demands=client_demands,
                               current_round=current_round,
                               current_round_stock=current_round_stock,
                               running_commands=running_commands,
                               state_game=state_game) 
     else:
        number_taken_actors = get_number_taken_actors(current_round,etape, name_supply_chain)
        return render_template('play/waiting_room.html',number_taken_actors=number_taken_actors)   

def post_step_1(name_supply_chain,generic_name,current_round):
    clients = db_session.execute(
    select(DeliveryCommand)
    .select_from(DeliveryCommand)
    .join(ClientSupplier, and_(ClientSupplier.name_client == DeliveryCommand.name_client, 
    ClientSupplier.name_supply_chain == DeliveryCommand.name_supply_chain, 
    ClientSupplier.name_supplier == DeliveryCommand.name_supplier ))
    .where(and_(DeliveryCommand.name_supplier == generic_name, 
    DeliveryCommand.name_supply_chain==name_supply_chain, 
    DeliveryCommand.round==current_round - ClientSupplier.command_time, #ça fonctionne car command_time=1
    DeliveryCommand.type=='command'))
    ).scalars().all()
    for client in clients:
        client.seen_by_actor = True
    db_session.commit()

    # On s'occupe du cas de Infinite Supplier si il n'a pas encore validé ses commandes
    clients = db_session.execute(
    select(DeliveryCommand)
    .select_from(DeliveryCommand)
    .join(ClientSupplier, and_(ClientSupplier.name_client == DeliveryCommand.name_client, 
    ClientSupplier.name_supply_chain == DeliveryCommand.name_supply_chain, 
    ClientSupplier.name_supplier == DeliveryCommand.name_supplier ))
    .where(and_(DeliveryCommand.name_supplier == 'Infinite Supplier', 
    DeliveryCommand.name_supply_chain==name_supply_chain, 
    DeliveryCommand.round==current_round - ClientSupplier.command_time, #ça fonctionne car command_time=1
    DeliveryCommand.type=='command'))
    ).scalars().all()
    for client in clients:
        client.seen_by_actor = True
    db_session.commit()

    return redirect(url_for('play.player_game'))

def get_step_2(name_supply_chain,generic_name,current_round,etape):
    # Si l'étape 2 n'a pas encore été validé
    commanded=db_session.execute(
            select(func.coalesce(func.sum(DeliveryCommand.quantity),0).label("quantity"),DeliveryCommand.name_client)
            .select_from(DeliveryCommand).join(ClientSupplier,and_(ClientSupplier.name_client == DeliveryCommand.name_client, ClientSupplier.name_supply_chain == DeliveryCommand.name_supply_chain, ClientSupplier.name_supplier == DeliveryCommand.name_supplier ))
            .where(and_(DeliveryCommand.name_supply_chain==name_supply_chain,
            DeliveryCommand.name_supplier==generic_name,
            DeliveryCommand.round+ClientSupplier.command_time<=current_round,
            DeliveryCommand.type=="command"))
            .group_by(DeliveryCommand.name_client)
    ).all()

    delivered=db_session.execute(
        select(func.coalesce(func.sum(DeliveryCommand.quantity),0).label("quantity"),DeliveryCommand.name_client)
        .select_from(DeliveryCommand).join(ClientSupplier,and_(ClientSupplier.name_client == DeliveryCommand.name_client, ClientSupplier.name_supply_chain == DeliveryCommand.name_supply_chain, ClientSupplier.name_supplier == DeliveryCommand.name_supplier ))
        .where(and_(DeliveryCommand.name_supply_chain==name_supply_chain,
        DeliveryCommand.name_supplier==generic_name,
        DeliveryCommand.round<current_round,
        DeliveryCommand.type=="delivery"))
        .group_by(DeliveryCommand.name_client)
    ).all()

    commands={}
    delivers={}
    #On va calculer le reste a livrer par client    
    for command in commanded : 
        name_client=command["name_client"]
        commands[name_client]=command["quantity"]

    for deliv in delivered :
        name_client=deliv["name_client"]
        delivers[name_client]=deliv["quantity"]

    rest_deliver={}
    max_rest_deliver=0

    for name_client in commands.keys():
        rest_deliver[name_client]=abs(commands[name_client]-delivers[name_client])
        if abs(commands[name_client]-delivers[name_client])>=max_rest_deliver:
            max_rest_deliver=abs(commands[name_client]-delivers[name_client])
    
    state_game = db_session.execute( # Pour changer l'état du bouton, True si la partie est finie
    select(SupplyChain.end_game)
    .select_from(SupplyChain)
    .where(and_(SupplyChain.name == name_supply_chain))
    ).scalars().first()
    current_round_stock = current_round_stock_find(current_round,generic_name,name_supply_chain,etape)
    running_commands = player_demands_not_sent(generic_name,name_supply_chain,current_round, etape)
    tracking_sheet_data = get_tracking_sheet_data(generic_name)
    return render_template('play/dashboard.html',data=tracking_sheet_data, rest_deliver=rest_deliver,etape=etape,current_round=current_round,current_round_stock=current_round_stock,running_commands=running_commands,state_game=state_game)

def post_step_2(name_supply_chain,generic_name,current_round,etape):

    # On vérifie si la ligne n'existe pas déjà
    nber_ligne_existante = db_session.execute(
    select(func.count(DeliveryCommand.name_supplier))
    .select_from(DeliveryCommand)
    .where(and_(DeliveryCommand.name_supply_chain == name_supply_chain, 
    DeliveryCommand.name_supplier == generic_name, 
    DeliveryCommand.type=='delivery', 
    DeliveryCommand.round ==current_round,
    DeliveryCommand.seen_by_actor=='False'))
    ).all()

    # On calcule le nombre de client du joueur 
    nber_clients_player = db_session.execute(
    select(func.count(ClientSupplier.name_supplier))
    .select_from(ClientSupplier)
    .where(and_(ClientSupplier.name_supplier == generic_name, 
    ClientSupplier.name_supply_chain == name_supply_chain))
    ).scalars().first()

    if nber_ligne_existante==nber_clients_player:
        number_taken_actors = get_number_taken_actors(current_round,etape, name_supply_chain)
        return render_template('play/waiting_room.html',number_taken_actors=number_taken_actors)
    else:

        clients = db_session.execute(
        select(ClientSupplier.name_client)
        .select_from(ClientSupplier)
        .where(and_(ClientSupplier.name_supply_chain == name_supply_chain, 
        ClientSupplier.name_supplier == generic_name))                
        ).all()
        somme=0
        quantity_clients = []
        for client in clients:
            new_delivery_command = DeliveryCommand(
            type='delivery',
            name_supplier=generic_name,
            name_supply_chain = name_supply_chain,
            name_client = client['name_client'],
            round = current_round,
            quantity = request.form.get(client['name_client'], ''),
            seen_by_actor = False
            )

            if request.form.get(client['name_client'], '') == '':
                erreur = 'Veuillez rentrer une valeur'
                flash(erreur)
                return redirect(url_for('play.player_game'))

            db_session.add(new_delivery_command)

            somme+=int(request.form.get(client['name_client'], ''))
            quantity_clients.append(int(request.form.get(client['name_client'], '')))
        
        # On rajoute les conditions d'erreurs
        erreur = None
        # Si la somme des livraisons à envoyer est supérieur au stock

        current_round_stock = current_round_stock_find(current_round,generic_name,name_supply_chain,etape)

        if current_round_stock < somme:
            erreur = "Il  n'y a pas assez de produits disponibles dans les stocks."
        # Si chaque livraison est plus grand que les restes à livrer totaux de chaque client

        # On détermine les restes à livrer de chaque client
        sum_command_received = db_session.execute(
        select(DeliveryCommand.name_client,func.coalesce(func.sum(func.coalesce(DeliveryCommand.quantity,0)),0).label('total_command'))
        .select_from(DeliveryCommand)
        .join(ClientSupplier)
        .where(and_(DeliveryCommand.name_supplier == generic_name, 
        DeliveryCommand.name_supply_chain==name_supply_chain, 
        DeliveryCommand.round<=current_round - ClientSupplier.command_time,
        DeliveryCommand.type=='command'))
        .group_by(DeliveryCommand.name_client)
        ).all()
        
        # On calcule la somme des livraisons des rounds de chaque client du joueur
        sum_delivery_sent = db_session.execute(
        select(DeliveryCommand.name_client,func.coalesce(func.sum(func.coalesce(DeliveryCommand.quantity,0)),0).label('total_delivery'))
        .select_from(DeliveryCommand)
        .where(and_(DeliveryCommand.name_supplier == generic_name, DeliveryCommand.name_supply_chain==name_supply_chain, 
        DeliveryCommand.round<current_round,DeliveryCommand.type=='delivery'))
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

        # On compare avec les quantités qu'on a mis
        for client in range (len(list_rest)):
            if list_rest[client]['total_rest'] < quantity_clients[client]:
                erreur = "Vous envoyez plus que ce que le joueur souhaite. Ce n'est pas bon.."
                break
        if erreur != None:
            flash(erreur)
            return redirect(url_for('play.player_game'))    
        else:   
            db_session.commit()
            
            return redirect(url_for('play.player_game'))
    # return a changer car on ne veux pas retourner un template dasn la methode post !!!

def get_step_3(client_delivery,etape,current_round,generic_name,name_supply_chain):
    if etape == 3:
        state_game = db_session.execute( # Pour changer l'état du bouton, True si la partie est finie
        select(SupplyChain.end_game)
        .select_from(SupplyChain)
        .where(and_(SupplyChain.name == name_supply_chain))
        ).scalars().first()
        
        running_commands = player_demands_not_sent(generic_name,name_supply_chain,current_round, etape)
        current_round_stock = current_round_stock_find(current_round,generic_name,name_supply_chain,etape)
        tracking_sheet_data = get_tracking_sheet_data(generic_name)
        return render_template('play/dashboard.html',data=tracking_sheet_data, delivery=client_delivery,etape=etape,current_round=current_round,current_round_stock=current_round_stock,running_commands=running_commands,state_game=state_game)
    elif etape==2:
        number_taken_actors = get_number_taken_actors(current_round,etape, name_supply_chain)
        return render_template('play/waiting_room.html',number_taken_actors=number_taken_actors)

def post_step_3(name_supply_chain,generic_name,current_round,etape):
    # On récupère la valeur du stock rentré par le joueur
    stock_computed = request.form.get('stock', '')
    current_round_stock = current_round_stock_find(current_round,generic_name,name_supply_chain,etape)
    if stock_computed == '':
        erreur = "Veuillez rentré une valeur de stock"
        flash(erreur)
        return redirect(url_for('play.player_game'))
    stock_player = int(stock_computed)
    if stock_player != current_round_stock:
        erreur = "La valeur n'est pas juste."
        flash(erreur)
        return redirect(url_for('play.player_game'))

    suppliers = db_session.execute(
    select(DeliveryCommand)
    .select_from(DeliveryCommand)
    .join(ClientSupplier, and_(ClientSupplier.name_client == DeliveryCommand.name_client, ClientSupplier.name_supply_chain == DeliveryCommand.name_supply_chain, ClientSupplier.name_supplier == DeliveryCommand.name_supplier ))
    .where(and_(DeliveryCommand.name_client == generic_name, 
    DeliveryCommand.name_supply_chain==name_supply_chain, 
    DeliveryCommand.round==current_round - ClientSupplier.delivery_time, #ça fonctionne car command_time=1
    DeliveryCommand.type=='delivery'))
    ).scalars().all()

    for supp in suppliers:
        supp.seen_by_actor = True
    db_session.commit()
    error=None
    return redirect(url_for('play.player_game'))
    # Pareil que pour post_step_2 on return pas de template dans la méthode post

def get_step_4(name_supply_chain,generic_name,etape,current_round):
    running_commands = player_demands_not_sent(generic_name,name_supply_chain,current_round, etape)
    current_round_stock = current_round_stock_find(current_round,generic_name,name_supply_chain,etape)
    variable_test = 'Un Test pour rentrer des variables avec des includes Code : ç_è-('
    # Noms des fournisseurs que possèdent le joueur 
    supplier_players = db_session.execute(
    select(ClientSupplier.name_supplier)
    .select_from(ClientSupplier)
    .where(and_(ClientSupplier.name_supply_chain == name_supply_chain, 
    ClientSupplier.name_client == generic_name))
    ).all()
    state_game = db_session.execute( # Pour changer l'état du bouton, True si la partie est finie
        select(SupplyChain.end_game)
        .select_from(SupplyChain)
        .where(and_(SupplyChain.name == name_supply_chain))
        ).scalars().first()
    tracking_sheet_data = get_tracking_sheet_data(generic_name)
    return render_template('play/dashboard.html',data=tracking_sheet_data, state_game=state_game,etape=etape, supplier_demands=supplier_players, name_supply_chain = name_supply_chain, variable_test1=variable_test,current_round_stock=current_round_stock,current_round=current_round,running_commands=running_commands)

def post_step_4(etape,nber_lines_delivery_command,name_supply_chain,generic_name,current_round,nber_suppliers_player,nber_clients_suppliers,client_deliveries,client_demands):
    # On vérifie si tous les joueurs ont validé
    # On vérifie si la ligne n'existe pas déjà
    nber_ligne_existante = db_session.execute(
    select(func.count(DeliveryCommand.name_client))
    .select_from(DeliveryCommand)
    .where(and_(DeliveryCommand.name_supply_chain == name_supply_chain, 
    DeliveryCommand.name_client == generic_name, 
    DeliveryCommand.type=='command', 
    DeliveryCommand.round ==current_round,
    DeliveryCommand.seen_by_actor=='False'))
    ).scalars().first()
    
    if nber_lines_delivery_command % (2 * nber_clients_suppliers) == 0 and client_deliveries[0]['seen_by_actor'] == True:
        return redirect(url_for('play.player_game'))
    # On vérifie si les lignes ont été validées déjà par le joueur
    if nber_ligne_existante == nber_suppliers_player:
        number_taken_actors = get_number_taken_actors(current_round,etape, name_supply_chain)
        return render_template('play/waiting_room.html',number_taken_actors=number_taken_actors)
    # Noms des fournisseurs que possèdent le joueur 
    suppliers = db_session.execute(
    select(ClientSupplier.name_supplier,ClientSupplier.name_client)
    .select_from(ClientSupplier)
    .where(and_(ClientSupplier.name_supply_chain == name_supply_chain, 
    ClientSupplier.name_client == generic_name))
    ).all()
 
    for supplier in suppliers:
        new_delivery_command = DeliveryCommand(
        type='command',
        name_client=generic_name,
        name_supply_chain = name_supply_chain,
        name_supplier = supplier[0],
        round = current_round,
        quantity = request.form.get(f"{supplier['name_supplier']}", ''),
        seen_by_actor = False
        )
        db_session.add(new_delivery_command)

    db_session.commit()
    # On vérifie si les lignes ont été validées à nouveau
    # Nombre de lignes dans la table Delivery_Command 
    nber_lines_delivery_command = db_session.execute(
    select(func.count(DeliveryCommand.name_client))
    .select_from(DeliveryCommand)
    .where(DeliveryCommand.name_supply_chain==name_supply_chain)
    ).scalars().first()
    # Si tous les joueurs ont validé

    if nber_lines_delivery_command % (2 * nber_clients_suppliers) == 0:
        return get_step_1(client_demands,etape)
    # Si toutes les lignes n'ont pas été validées
    else:
        number_taken_actors = get_number_taken_actors(current_round,etape, name_supply_chain)
        return render_template('play/waiting_room.html',number_taken_actors=number_taken_actors)

def is_everyone_ready(name_supply_chain):
    # Nombre de lignes dans la table Delivery_Command depuis le 1er round
    nber_lines_delivery_command = db_session.execute(
    select(func.count(DeliveryCommand.name_client))
    .select_from(DeliveryCommand)
    .where(DeliveryCommand.round > 0)
    .where(DeliveryCommand.name_supply_chain == name_supply_chain)
    ).scalars().first()

    # Nombre de relations clients_fournisseurs 
    nber_clients_suppliers = db_session.execute(
    select(func.count(ClientSupplier.name_client))
    .select_from(ClientSupplier)
    ).scalars().first()
    # Étape 4
    # Si tous les joueurs ont rentré leurs commandes, on le renvoit vers le dashboard et donc True
    if nber_lines_delivery_command % (2 * nber_clients_suppliers) == 0:
        return True
        #return redirect(url_for('play.player_game'))
    # Si tous les joueurs n'ont pas fini de rentrer leur commandes et que donc tout le monde n'a pas fini de valider
    elif nber_lines_delivery_command % (2 * nber_clients_suppliers) >= nber_clients_suppliers:
        return False

def step_4_validated(name_supply_chain,generic_name,current_round,nber_suppliers_player):

    # On vérifie si la ligne n'existe pas déjà
    nber_ligne_existante = db_session.execute(
    select(func.count(DeliveryCommand.name_client))
    .select_from(DeliveryCommand)
    .where(and_(DeliveryCommand.name_supply_chain == name_supply_chain, 
    DeliveryCommand.name_client == generic_name, 
    DeliveryCommand.type=='command', 
    DeliveryCommand.round ==current_round,
    DeliveryCommand.seen_by_actor=='false'))
    ).scalars().first()

    return nber_ligne_existante == nber_suppliers_player

def step_2_not_validated(current_round,generic_name,name_supply_chain):
    test=db_session.execute(
        select(DeliveryCommand)
        .select_from(DeliveryCommand)
        .where(and_(DeliveryCommand.name_supply_chain==name_supply_chain,
        DeliveryCommand.name_supplier==generic_name,
        DeliveryCommand.type=="delivery",
        DeliveryCommand.round==current_round))
    ).scalars().first()
    return test==None

def current_round_stock_find(current_round,generic_name,name_supply_chain,etape):
        # On calcule le stock du joueur
        # On détermine le stock intial du joueur
        initial_stock = db_session.execute(
        select(Actor.initial_stock)
        .select_from(Actor)
        .where(and_(Actor.generic_name == generic_name, 
        Actor.name_supply_chain==name_supply_chain)
        )).scalars().first()
        
        if etape==3 or etape==4:
            sum_delivery_received = db_session.execute(
            select(func.coalesce(func.sum(func.coalesce(DeliveryCommand.quantity,0)),0).label('total_delivery'))
            .select_from(DeliveryCommand)
            .join(ClientSupplier)
            .where(and_(DeliveryCommand.name_client == generic_name, 
            DeliveryCommand.name_supply_chain==name_supply_chain, 
            DeliveryCommand.round <= current_round-ClientSupplier.delivery_time,
            DeliveryCommand.round>0,
            DeliveryCommand.type=='delivery'))
            ).scalars().first()
        elif etape==1 or etape==2:
            sum_delivery_received = db_session.execute(
            select(func.coalesce(func.sum(func.coalesce(DeliveryCommand.quantity,0)),0).label('total_delivery'))
            .select_from(DeliveryCommand)
            .join(ClientSupplier)
            .where(and_(DeliveryCommand.name_client == generic_name, 
            DeliveryCommand.name_supply_chain==name_supply_chain, 
            DeliveryCommand.round < current_round-ClientSupplier.delivery_time,
            DeliveryCommand.type=='delivery'),
            DeliveryCommand.round>0)
            ).scalars().first()
         

        # On fait la somme de toutes les livraisons envoyées par le joueur
        sum_delivery_sent_all_players = db_session.execute(
        select(func.coalesce(func.sum(DeliveryCommand.quantity),0).label('total_delivery'))
        .select_from(DeliveryCommand)
        .where(and_(DeliveryCommand.name_supplier == generic_name, 
        DeliveryCommand.name_supply_chain==name_supply_chain, 
        DeliveryCommand.round<= current_round,
        DeliveryCommand.round > 0,
        DeliveryCommand.type=='delivery'))
        ).scalars().first()
        
        current_round_stock = (initial_stock + sum_delivery_received - sum_delivery_sent_all_players) 
        
        return current_round_stock

def current_round_find(name_supply_chain):
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
    current_round = floor(nber_lines_delivery_command / (2*nber_clients_suppliers)) + 1
    return current_round

# Pour afficher les commandes en cours
def player_demands_not_sent(generic_name,name_supply_chain,current_round, etape):
    if etape==3 or etape==4:
        # On récupère demandes envoyées par le joueur 
        player_demands = db_session.execute(
        select(DeliveryCommand.name_supplier,DeliveryCommand.name_client, DeliveryCommand.quantity, (DeliveryCommand.round + ClientSupplier.command_time + ClientSupplier.delivery_time).label('round_received'), DeliveryCommand.seen_by_actor)
        .select_from(DeliveryCommand)
        .join(ClientSupplier, and_(ClientSupplier.name_client == DeliveryCommand.name_client, 
        ClientSupplier.name_supply_chain == DeliveryCommand.name_supply_chain, 
        ClientSupplier.name_supplier == DeliveryCommand.name_supplier ))
        .where(and_(DeliveryCommand.name_client == generic_name, 
        DeliveryCommand.name_supply_chain==name_supply_chain, 
        DeliveryCommand.round + ClientSupplier.command_time + ClientSupplier.delivery_time > current_round, #ça fonctionne car command_time=1
        DeliveryCommand.type=='command'))
        ).all()

    elif etape==1 or etape==2:
        # On récupère demandes envoyées par le joueur 
        player_demands = db_session.execute(
        select(DeliveryCommand.name_supplier,DeliveryCommand.name_client, DeliveryCommand.quantity, (DeliveryCommand.round + ClientSupplier.command_time + ClientSupplier.delivery_time).label('round_received'), DeliveryCommand.seen_by_actor)
        .select_from(DeliveryCommand)
        .join(ClientSupplier, and_(ClientSupplier.name_client == DeliveryCommand.name_client, 
        ClientSupplier.name_supply_chain == DeliveryCommand.name_supply_chain, 
        ClientSupplier.name_supplier == DeliveryCommand.name_supplier ))
        .where(and_(DeliveryCommand.name_client == generic_name, 
        DeliveryCommand.name_supply_chain==name_supply_chain, 
        DeliveryCommand.round + ClientSupplier.command_time + ClientSupplier.delivery_time >= current_round, #ça fonctionne car command_time=1
        DeliveryCommand.type=='command'))
        ).all()
    return player_demands

def tracking_sheet(name_supply_chain,generic_name):
    #generic_name = 'Central Distribution Center'
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
    client_deliveries = db_session.execute(
    select(DeliveryCommand.name_supplier, DeliveryCommand.quantity, DeliveryCommand.seen_by_actor)
    .select_from(DeliveryCommand)
    .join(ClientSupplier, and_(ClientSupplier.name_client == DeliveryCommand.name_client, 
    ClientSupplier.name_supply_chain == DeliveryCommand.name_supply_chain, 
    ClientSupplier.name_supplier == DeliveryCommand.name_supplier ))
    .where(and_(DeliveryCommand.name_client == generic_name, 
    DeliveryCommand.name_supply_chain==name_supply_chain, 
    DeliveryCommand.round==current_round - ClientSupplier.delivery_time,
    DeliveryCommand.type=='delivery',DeliveryCommand.round>0))
    ).all()
    
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
    etape = 4
        # On récupère la demande des clients du joueur
    for round in round_list:
        
        if round < current_round:
            round_line = {}
            # On récupère les demandes clients du joueur
            # ça fonctionne
            client_demands = db_session.execute(
            select(DeliveryCommand.name_client, func.coalesce(DeliveryCommand.quantity,0), DeliveryCommand.seen_by_actor)
            .select_from(DeliveryCommand)
            .join(ClientSupplier, and_(ClientSupplier.name_client == DeliveryCommand.name_client, 
            ClientSupplier.name_supply_chain == DeliveryCommand.name_supply_chain, 
            ClientSupplier.name_supplier == DeliveryCommand.name_supplier ))
            .where(and_(DeliveryCommand.name_supplier == generic_name, 
            DeliveryCommand.name_supply_chain==name_supply_chain, 
            DeliveryCommand.round== round - ClientSupplier.command_time, #ça fonctionne car command_time=1
            DeliveryCommand.type=='command'))
            ).all()
            client_demands=client_demands.scalars().first()
            round_line['client_demands'] = client_demands

            # On récupère les livraisons que va envoyer le joueur
            # ça fonctionne
            player_deliveries = db_session.execute(
            select(DeliveryCommand.name_client, func.coalesce(DeliveryCommand.quantity,0))
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
            select(DeliveryCommand.name_client, DeliveryCommand.quantity, DeliveryCommand.seen_by_actor)
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
            if etape >= 2:
                # On récupère les demandes clients du joueur
                client_demands = db_session.execute(
                select(DeliveryCommand.name_client, func.coalesce(DeliveryCommand.quantity,0), DeliveryCommand.seen_by_actor)
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
                select(DeliveryCommand.name_client, func.coalesce(DeliveryCommand.quantity,0))
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
                select(func.sum(func.coalesce(DeliveryCommand.quantity,0)).label('total_delivery'))
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

    return data, round_list, etape
    
