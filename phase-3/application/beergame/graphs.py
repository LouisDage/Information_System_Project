import functools
from math import *
from random import randint
#from ast import Del
from multiprocessing.connection import Client

from sqlalchemy import select, func, and_

from beergame.db import DeliveryCommand, db_session, Actor,ClientSupplier


def graph(name_supply_chain):
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

    return list_player_rest_penalty, list_player_rest_penalty_cumulated, list_player_stock_penalty, list_player_stock_penalty_cumulated, round_list,nber_round, list_player_stock_and_rest_penalty, list_player_stock_and_rest_penalty_cumulated