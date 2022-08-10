from crypt import methods
from random import randint

from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, session
)
from werkzeug.security import (check_password_hash, generate_password_hash )
from werkzeug.exceptions import abort
from sqlalchemy import select, bindparam, func, and_
from sqlalchemy.orm import aliased

from beergame.function_util import *
from beergame.step import *
from beergame.db import DeliveryCommand, SupplyChain, db_session, Actor,ClientSupplier
from beergame.utils import get_all_players_from_one_supply_chain


bp = Blueprint('play', __name__,url_prefix="/play")


@bp.route('/lobby', methods=("GET", "POST"))
def lobby_player():
    '''
     Cette route a pour objectif de nous amener sur la page du salon d'un joueur
     Cette route permettra également de choisir un joueur, son nom d'entreprise, son mot de passe
     Tout cela, tout en maintenant la cohérence de la Table Actor ainsi que la vérification du mot de passe
    '''
    
    # On récupère le nom de la supply chain pour associer le joueur à la bonne supply chain
    name_supply_chain = session.get("name_supply_chain")

    # On récupère les acteurs de la chaîne qui n'ont pas encore été choisis
    actor_available = db_session.execute(
    select(Actor.generic_name)
    .select_from(Actor)
    .where(and_(Actor.firm_name == '',Actor.name_supply_chain==name_supply_chain, Actor.type=="player"))
    ).all()

    if request.method == "POST":
    
        # On récupère le nom de l'entreprise imaginé par le joueur
        firmname = request.form.get("firmname", '').strip()

        # On récupère l'acteur que le joueur a choisi
        genericname = request.form.get("actor", '').strip()

        # On récupère le mot de passe que le joueur a rentré
        password = request.form.get("password", '').strip()
        
        # On récupère la confirmation de mot de passe afin de vérifier qu'il a bien rentré le bon mot de passe
        confirmedpassword = request.form.get("confirmedpassword", '').strip()
        
        error = None
        
        # Si l'utilisateur s'est trompé lors de l'entrée du mot de passe
        if password != confirmedpassword:
            error = 'Les mots de passe ne correspondent pas'
            flash(error)
            return redirect(url_for('play.lobby_player'))
        
        # Si l'utilisateur a oublié de mettre un nom d'entreprise
        if firmname == '':
            error = "Le nom d'entreprise est obligatoire."
            flash(error)
            return redirect(url_for('play.lobby_player'))

        # Si l'utilisateur a oublié de mettre un mot de passe
        if password == '':
            error = 'Le mot de passe est obligatoire.'
            flash(error)
            return redirect(url_for('play.lobby_player'))

    # Si le joueur a correctement rentré le nom d'entreprise, 
    # le mot de passe et la confirmation de mot de passe
        if error is None:
            # On vérifie qu'un joueur de la partie ne porte pas déjà le nom donné par l'utilisateur
            actor_same = db_session.execute(
            select(func.count(Actor.generic_name))
            .select_from(Actor)
            .where(and_(Actor.firm_name == firmname,Actor.name_supply_chain==name_supply_chain, Actor.type=="player"))
            ).scalars().first()
        
        # Si il existe au moins un acteur qui a déjà ce nom de partie, on lui demande de choisir à nouveau
        if actor_same != 0:
            error = "Ce nom d'entreprise a déjà été choisi."
            flash(error)
            return redirect(url_for('play.lobby_player'))
        # Si le nom n'a jamais été choisi
        else:
            # On vérifie qu'il n'y a pas un acteur qui possède déjà l'acteur
            actor_same = db_session.execute(
            select(func.count(Actor.generic_name))
            .select_from(Actor)
            .where(and_(Actor.generic_name == genericname,Actor.name_supply_chain==name_supply_chain, Actor.firm_name!='',Actor.type=="player"))
            ).scalars().first()
            # On met à jour dans la base de donnée
            if actor_same > 0:
                erreur = "L'acteur a déjà été choisi, veuillez en choisir un autre ."
                flash(erreur)
                return redirect(url_for('play.lobby_player'))

            db_session.query(Actor).\
            filter(Actor.generic_name == genericname).\
            filter(Actor.name_supply_chain == name_supply_chain).\
            update({"firm_name": firmname, "password":generate_password_hash(password)})
            db_session.commit()
            # On enregistre pour pouvoir les utiliser pendant la partie
            session["actor_firm_name"] = firmname
            session["actor_generic_name"] = genericname
            # Ici on devra avoir la route pour le chargement de la partie
            return redirect(url_for('play.waiting_room'))
    return render_template('play/lobby.html',actor_available=actor_available,name_supply_chain=name_supply_chain) # posts=posts)

    #     #sort_order = request.args.get('sort', 'by_date')

    #     #Star2 = aliased(Star) # Pour voir des jointures avec la même table par exemple
    #     #orders = dict(
    #     #    by_date=Post.created.desc(),
    #     #    by_star=func.count(Star.user_id).desc(),
    #     #)
    #     #if sort_order not in orders.keys():
    #     #    sort_order = 'by_date'
    #return render_template('play/lobby.html') # posts=posts)
    #elif not check_password_hash(user.password, password):
    #        error = "Incorrect password."

# La session fonctionne !
# Permet de rejoindre une partie
@bp.route('/join', methods=("GET", "POST"))
def join():
    if request.method == "POST":
        name_supply_chain = request.form.get("name_supply_chain", '').strip() # Nom de la variable du formulaire permettant de donner le nom de la partie
        # Si le joueur veut se connecter à une partie et qu'il a déjà un compte sur cette partie
        firm_name = request.form.get("firmname",'').strip()
        password_firm = request.form.get("password",'').strip()

        #  #"Hello, %s. You are %s." % (name, age)
        error = None

        # On affiche une erreur si le nom de la partie n'est pas donné
        if name_supply_chain == '':
              error = 'Le nom de la partie est obligatoire'
        
        # Si il y a une erreur
        if error is not None:
            flash(error)
            return render_template('play/join.html')
        
        # Si il n'y a pas d'erreur dans l'entrée des données
        else:
            # On vérifie que le nom de la partie existe dans la base de données
            supply_chain = db_session.execute(
            select(SupplyChain).
            where(SupplyChain.name == name_supply_chain)
            ).scalars().first()
            db_session.commit() # Permet d'enregistrer un élément dans la base de données
            
            # Message d'erreur si la partie n'existe pas
            if supply_chain == None:
                error = "La partie ou le mot de passe n'est pas valide."
                flash(error)
                return render_template('play/join.html')
            # Si la partie existe
            else:
                name_supply_chain = supply_chain.name

                # Si le joueur veut se créer un compte dans la Partie
                if firm_name =='' and password_firm =='':
                    
                    name_supply_chain = supply_chain.name
                    # récupérer plus tard le nombre d'acteurs disponibles grâce à la variable actor_available
                    actor_number_incomplete = db_session.execute(
                    select(func.count(firm_name))
                    .select_from(Actor)
                    .where(and_(Actor.firm_name == '',Actor.name_supply_chain==name_supply_chain, Actor.type=="player"))
                    ).scalars().first()
                    # Les acteurs disponibles
                    actor_available = db_session.execute(
                    select(Actor.generic_name)
                    .select_from(Actor)
                    .where(and_(Actor.firm_name == '',Actor.name_supply_chain==name_supply_chain, Actor.type=="player"))
                    ).all()
                    # si il n'y a de rôle possible
                    if actor_number_incomplete == 0:
                        error = 'Le nombre de joueur est complet.'
                        flash(error)
                        return render_template('play/join.html')
                    
                    # Sinon on le renvoit dans vers le salon 
                    else:
                        session['name_supply_chain'] = name_supply_chain
                        return redirect(url_for('play.lobby_player'))
                  
                # Si l'utilisateur a déjà un compte existant pour cette partie
                else:
                    name_supply_chain = supply_chain.name
                    # On récupère l'acteur si il existe
                    actor_chosen = db_session.execute(
                    select(Actor)
                    .select_from(Actor)
                    .where(and_(Actor.firm_name == firm_name,Actor.name_supply_chain==name_supply_chain))
                    ).scalars().first()
                    
                    # Si le joueur n'existe pas
                    if actor_chosen == None:
                        error = "Le mot de passe ou le nom d'utilisateur est incorrect."
                        flash(error)
                        return render_template('play/join.html')

                    # Si le mot de passe n'est pas just 
                    elif not check_password_hash(actor_chosen.password, password_firm):
                        error = "Le mot de passe ou le nom d'utilisateur est incorrect."
                        flash(error)
                        return render_template('play/join.html')
                    # Si l'utilisateur a rentré les bonnes données du joueur existant
                    else:
                        name_supply_chain = supply_chain.name
                        actor_number_incomplete = db_session.execute(
                        select(func.count(firm_name))
                        .select_from(Actor)
                        .where(and_(Actor.firm_name == '',Actor.name_supply_chain==name_supply_chain, Actor.type=="player"))
                        ).scalars().first()
                        session['name_supply_chain'] = name_supply_chain
                        session['actor_generic_name'] = actor_chosen.generic_name
                        session['actor_firm_name'] = firm_name
                        # Si la partie n'a pas encore commencé
                        if actor_number_incomplete != 0:
                            return render_template('play/waiting_room.html') # Le nom changera
                        # Si la partie a déjà commencé
                        else:
                            return redirect(url_for('play.player_game')) # Le compte de la partie changera
    return render_template('play/join.html')

@bp.route('/dashboard', methods=("GET","POST"))
def dashboard():
    return render_template('play/dashboard.html')

@bp.route('/player_game',methods=('GET','POST'))
def player_game():
    # On récupère les données de la session
    name_supply_chain = session['name_supply_chain']
    firm_name = session["actor_firm_name"] 
    generic_name =  session["actor_generic_name"] 
    
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
    

    # Nombre de fournniseurs du joueur
    nber_suppliers_player = db_session.execute(
    select(func.count(ClientSupplier.name_supplier))
    .select_from(ClientSupplier)
    .where(and_(ClientSupplier.name_client == generic_name, 
    ClientSupplier.name_supply_chain == name_supply_chain))
    ).scalars().first()

    # On récupère les demandes clients du joueur
    client_demands = get_client_demands(name_supply_chain,current_round,generic_name)
    
    #  db_session.execute(
    # select(DeliveryCommand.name_client, DeliveryCommand.quantity, DeliveryCommand.seen_by_actor)
    # .select_from(DeliveryCommand)
    # .join(ClientSupplier, and_(ClientSupplier.name_client == DeliveryCommand.name_client, 
    # ClientSupplier.name_supply_chain == DeliveryCommand.name_supply_chain, 
    # ClientSupplier.name_supplier == DeliveryCommand.name_supplier ))
    # .where(and_(DeliveryCommand.name_supplier == generic_name, 
    # DeliveryCommand.name_supply_chain==name_supply_chain, 
    # DeliveryCommand.round==current_round - ClientSupplier.command_time, #ça fonctionne car command_time=1
    # DeliveryCommand.type=='command'))
    # ).all()

    # On récupère les livraisons du joueur
    client_deliveries = get_client_deliveries(name_supply_chain,current_round,generic_name)
    # db_session.execute(
    # select(DeliveryCommand.name_supplier, DeliveryCommand.quantity, DeliveryCommand.seen_by_actor)
    # .select_from(DeliveryCommand)
    # .join(ClientSupplier, and_(ClientSupplier.name_client == DeliveryCommand.name_client, 
    # ClientSupplier.name_supply_chain == DeliveryCommand.name_supply_chain, 
    # ClientSupplier.name_supplier == DeliveryCommand.name_supplier ))
    # .where(and_(DeliveryCommand.name_client == generic_name, 
    # DeliveryCommand.name_supply_chain==name_supply_chain, 
    # DeliveryCommand.round==current_round - ClientSupplier.delivery_time,
    # DeliveryCommand.type=='delivery'))
    # ).all()

    etape = get_etape(nber_lines_delivery_command,nber_clients_suppliers,client_demands,client_deliveries)
    if request.method=='POST':
        if etape==1:
            return post_step_1(name_supply_chain,generic_name,current_round)
        elif etape==2:
            if step_2_not_validated(current_round,'Infinite Supplier',name_supply_chain):
                # On récupère les commandes de infinite supplier
                client_demands =  get_client_demands(name_supply_chain,current_round,'Infinite Supplier')
        
                for client in client_demands:
                    new_delivery_command = DeliveryCommand(
                    type='delivery',
                    name_supplier='Infinite Supplier',
                    name_supply_chain = name_supply_chain,
                    name_client = client['name_client'],
                    round = current_round,
                    quantity = client['quantity'],
                    seen_by_actor = False
                    )
                    db_session.add(new_delivery_command)

                db_session.commit()
            return post_step_2(name_supply_chain,generic_name,current_round,etape)
            #return get_step_3(client_deliveries,etape)
        elif etape==3:
            return post_step_3(name_supply_chain,generic_name,current_round,etape)
        elif etape==4:
            return post_step_4(etape,nber_lines_delivery_command,name_supply_chain,generic_name,current_round,nber_suppliers_player,nber_clients_suppliers,client_deliveries,client_demands)
            #return get_step_1(client_demands,etape)
    else:
        if etape==1:
            return get_step_1(client_demands,etape,current_round, generic_name,name_supply_chain)
        elif etape==2:
            # Si le joueur n'a pas encore validé  l'étape 2
            if step_2_not_validated(current_round,generic_name,name_supply_chain):
                return get_step_2(name_supply_chain,generic_name,current_round,etape)
            # Si le joueur a tout validé 
            else:
                number_taken_actors = get_number_taken_actors(current_round,etape, name_supply_chain)
                return render_template('play/waiting_room.html',number_taken_actors=number_taken_actors)
        elif etape==3:
            return get_step_3(client_deliveries,etape,current_round,generic_name,name_supply_chain)
        elif etape==4:
            # Si tout le monde a validé ses commandes, on passe à l'étape suivante
            if is_everyone_ready(name_supply_chain):
            #if nber_lines_delivery_command % (2 * nber_clients_suppliers) == 0 and client_deliveries[0]['seen_by_actor'] == True:
                return get_step_1(client_demands,etape,current_round, generic_name,name_supply_chain)
            # Si le joueur a déjà validé ses commandes
            elif step_4_validated(name_supply_chain,generic_name,current_round,nber_suppliers_player):
                number_taken_actors = get_number_taken_actors(current_round,etape, name_supply_chain)
                return render_template('play/waiting_room.html', number_taken_actors=number_taken_actors)
            # Si le joueur n'a pas validé ses commandes
            else:
                return get_step_4(name_supply_chain,generic_name,etape,current_round)

@bp.route('/waiting_room', methods=("GET","POST"))
def waiting_room():
    number_taken_actors = db_session.execute(
        select(func.count(Actor.generic_name))
        .where(and_(Actor.firm_name != '',Actor.name_supply_chain==session["name_supply_chain"], Actor.type=="player"))
    ).scalars().first()

    if request.method == "POST":
        return render_template('play/player_task.html', number_taken_actors=number_taken_actors)
    
    return render_template('play/waiting_room.html', number_taken_actors=number_taken_actors)

@bp.route('/game_rules', methods=("GET", ))
def player_game_rules():
    return render_template('game_rules.html')

@bp.route('/tracking_sheet', methods=("GET","POST"))
def tracking_sheet():
    # On récupère la liste de rounds
    if methods=='POST':
        generic_name = request.form.get("actor_name", '').strip()
    elif session["actor_generic_name"]:
        generic_name = session["actor_generic_name"]


    name_supply_chain = session['name_supply_chain']
    # if session["actor_generic_name"]:
    #     generic_name = session["actor_generic_name"]
    # else:
    #     generic_name = request.form.get("actor_name", '').strip()
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
    client_deliveries = get_client_deliveries(name_supply_chain,current_round,generic_name)
    
    # db_session.execute(
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
    client_demands = get_client_demands(name_supply_chain,current_round,generic_name)
    # db_session.execute(
    # select(DeliveryCommand.name_client, DeliveryCommand.quantity, DeliveryCommand.seen_by_actor)
    # .select_from(DeliveryCommand)
    # .join(ClientSupplier, and_(ClientSupplier.name_client == DeliveryCommand.name_client, 
    # ClientSupplier.name_supply_chain == DeliveryCommand.name_supply_chain, 
    # ClientSupplier.name_supplier == DeliveryCommand.name_supplier ))
    # .where(and_(DeliveryCommand.name_supplier == generic_name, 
    # DeliveryCommand.name_supply_chain==name_supply_chain, 
    # DeliveryCommand.round== current_round - ClientSupplier.command_time, #ça fonctionne car command_time=1
    # DeliveryCommand.type=='command',
    # ))
    # ).all()
    if nber_lines_delivery_command % (2 * nber_clients_suppliers) == 0 and client_demands[0]['seen_by_actor'] == False:
        etape = 1
    elif nber_lines_delivery_command % (2 * nber_clients_suppliers) >= nber_clients_suppliers and client_deliveries[0]['seen_by_actor'] == True:
        etape = 4
    # On est à l'étape 1
    etape=4
        # On récupère la demande des clients du joueur
    for round in round_list:
        
        if round < current_round:
            round_line = {}
            # On récupère le round
            round_line['round'] = round
            # On récupère les demandes clients du joueur
            # ça fonctionne
            client_demands = get_client_demands(name_supply_chain,current_round,generic_name)
            
            # db_session.execute(
            # select(DeliveryCommand.name_client, func.coalesce(DeliveryCommand.quantity,0), DeliveryCommand.seen_by_actor)
            # .select_from(DeliveryCommand)
            # .join(ClientSupplier, and_(ClientSupplier.name_client == DeliveryCommand.name_client, 
            # ClientSupplier.name_supply_chain == DeliveryCommand.name_supply_chain, 
            # ClientSupplier.name_supplier == DeliveryCommand.name_supplier ))
            # .where(and_(DeliveryCommand.name_supplier == generic_name, 
            # DeliveryCommand.name_supply_chain==name_supply_chain, 
            # DeliveryCommand.round== round - ClientSupplier.command_time, #ça fonctionne car command_time=1
            # DeliveryCommand.type=='command'))
            # ).all()
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
                client_demands = get_client_demands(name_supply_chain,current_round,generic_name)
                # db_session.execute(
                # select(DeliveryCommand.name_client, func.coalesce(DeliveryCommand.quantity,0), DeliveryCommand.seen_by_actor)
                # .select_from(DeliveryCommand)
                # .join(ClientSupplier, and_(ClientSupplier.name_client == DeliveryCommand.name_client, 
                # ClientSupplier.name_supply_chain == DeliveryCommand.name_supply_chain, 
                # ClientSupplier.name_supplier == DeliveryCommand.name_supplier ))
                # .where(and_(DeliveryCommand.name_supplier == generic_name, 
                # DeliveryCommand.name_supply_chain==name_supply_chain, 
                # DeliveryCommand.round== round - ClientSupplier.command_time, #ça fonctionne car command_time=1
                # DeliveryCommand.type=='command'))
                # ).all()

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
    ## Il faut que l'on fasse une disjonction de cas lorsque la liste des demandes clients est vide est qu'il faille mettre 0 à la place
    return render_template('play/tracking_sheet.html',data=data,etape=etape)

@bp.route("/graphs", methods = ("GET",))
def graphs():
    
    name_supply_chain = session['name_supply_chain']
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

    return render_template("supervise/graphics.html",
    list_player_rest_penalty = list_player_rest_penalty ,
    list_player_rest_penalty_cumulated = list_player_rest_penalty_cumulated, 
    list_player_stock_penalty = list_player_stock_penalty , 
    list_player_stock_penalty_cumulated = list_player_stock_penalty_cumulated, 
    round_list = round_list, nber_round =nber_round, 
    list_player_stock_and_rest_penalty = list_player_stock_and_rest_penalty, 
    list_player_stock_and_rest_penalty_cumulated =  list_player_stock_and_rest_penalty_cumulated)
