-- Initialize the database.
-- Drop any existing data and create empty tables.
-- 
-- psql "postgresql://beergamegadmin:beergameadminpass@localhost:5432/beergame" < beergame/schema-postgresql.sql
-- 

drop table if exists delivery_command cascade;
drop table if exists client_supplier cascade;
drop table if exists actor cascade;
drop table if exists supply_chain cascade; --game remplacé par supply chain
drop table if exists supervisor cascade;
drop type if exists actor_type cascade;
drop type if exists delcom cascade;

CREATE TYPE actor_type AS ENUM ('universal_supplier','player','universal_client');
CREATE TYPE delcom AS ENUM ('delivery', 'command');

create table supervisor (
        id serial primary key, -- serial permet d'auto incrémenter l'id au remplissage de la table et primary key permet de le rendre unique 
        username text unique not null, 
        password text not null,
        client_demand int, --demande du superviseur pour les commandes
        administrator bool,
        validation_round bool DEFAULT false
        );

create table supply_chain (
	name text primary key, 
        id_supervisor integer not null,
        total_round_number integer not null  CHECK (total_round_number>0), -- correspond au nombre total de round que l'on peut avoir dans une partie
        --name text unique not null, -- unicité du nom de la partie   
        penality_stock integer  CHECK (penality_stock>0), -- pénalité de stock que l'on peut appliquer pour un produit 
        penality_late integer  CHECK (penality_late>0), --également pour une unité de produit
        end_game bool not null,
        CONSTRAINT supervised_by foreign key (id_supervisor) references supervisor (id) on update cascade -- on associera le jeu au superviseur créateur de la partie
        );
        
create table actor (
	primary key (generic_name, name_supply_chain),
        generic_name text not null,
        firm_name text, -- firm_name peut être nulle
        initial_stock integer not null,
        password text not null,
        type actor_type not null,
        name_supply_chain text not null,
        CONSTRAINT integrated_in foreign key (name_supply_chain) references supply_chain (name) on update cascade
        );
           
     
create table client_supplier (
	primary key (name_client, name_supplier,name_supply_chain), -- la clé sera une association entre deux acteurs : l'un jouant le rôle de client par rapport à l'autre, cependant si client est non identifié
        command_time integer not null
        CHECK (command_time > 0), 
        delivery_time integer not null
        CHECK (delivery_time > 0),
        name_client text not null,
        name_supply_chain text not null,
        name_supplier text not null, 
        CONSTRAINT to_client foreign key (name_client,name_supply_chain) references actor (generic_name,name_supply_chain),
        CONSTRAINT to_supplier foreign key (name_supplier, name_supply_chain) references actor (generic_name,name_supply_chain)
        );

create table delivery_command (
	primary key (type,"round", name_client, name_supplier, name_supply_chain), --les pénalités dépendent du joueur qui doit se trouver dans une certaine partie 
        type delcom not null, 
        "round" integer, -- le round peut être vide à l'initialisation
        --CONSTRAINT max_round CHECK (round < total_round+1), -- total round récupérer de la table supply_chain ?
        name_client text not null,
        name_supply_chain text not null,
        name_supplier text not null,
        quantity integer, -- Les quantités que l'on demande pour la livraison
        seen_by_actor bool,
        --foreign key (total_round) references supply_chain (total_round_number),  
        CONSTRAINT interaction_between foreign key (name_client, name_supplier, name_supply_chain) references client_supplier (name_client, name_supplier, name_supply_chain) on update cascade
        );
        
-- ON VA INSERER NOS LIGNES 

