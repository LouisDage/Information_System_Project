INSERT INTO supervisor (username, password,client_demand,administrator) VALUES
('polo', 'pbkdf2:sha256:150000$yYDumTmh$dd0b82d936ec3d5058f43809d2e1b363d41f9b158039b58921c67ac19042391f',1,false),
('toto', 'pbkdf2:sha256:150000$tXe6g8kL$bb202dd48e19184b234132628a23807ff128d7c3c5d2aa4d2eccb55c50ba5a9f',1,false),
('toto_step', 'pbkdf2:sha256:260000$ZNvmLzCqMrdV7yfF$97fc75e132f304a75e1a1c920a8d1dbc47bfc832a104b084b17b74d1998cbd77',1,false);
INSERT INTO supply_chain ("name","id_supervisor", "total_round_number","penality_stock","penality_late", "end_game") VALUES ---
('test',1,4,1,1,false), 
('complete_chain',1,4,1,1,false),
('test2',1,4,1,1,false),
('test3',3,4,1,1,false);

INSERT INTO actor (generic_name, firm_name, initial_stock, password,type,name_supply_chain) VALUES
('toto','toto_firm',1,'2020-12-22 09:17:09.93821', 'player', 'test'),
('toto2','toto_firm2',1, '2020-12-22 10:04:07.47829','player', 'test'),
('toto3','',1, '','player', 'test'),
('toto4','existing_firm',1, 'pbkdf2:sha256:150000$yYDumTmh$dd0b82d936ec3d5058f43809d2e1b363d41f9b158039b58921c67ac19042391f','player','complete_chain'),
('toto','toto_firm',1,'2020-12-22 09:17:09.93821', 'player', 'test2'),
('toto9','existing_firm',1, 'pbkdf2:sha256:150000$tXe6g8kL$bb202dd48e19184b234132628a23807ff128d7c3c5d2aa4d2eccb55c50ba5a9f','player','test');



INSERT INTO actor (generic_name, firm_name, initial_stock, password,type,name_supply_chain) VALUES
('toto','toto_firm',1,'2020-12-22 09:17:09.93821', 'player', 'complete_chain'),
('toto2','toto_firm2',1, '2020-12-22 10:04:07.47829','player', 'complete_chain'),
('toto3','toto_firm3',1,'2020-12-22 09:17:09.93821', 'player', 'complete_chain'),
--('toto4','existing_firm',1, '2020-12-22 10:04:07.47829','player', 'complete_chain'),--
('toto5','toto_firm5',1,'2020-12-22 09:17:09.93821', 'player', 'complete_chain'),
('toto6','toto_firm6',1, '2020-12-22 10:04:07.47829','player', 'complete_chain'),
('toto7','toto_firm7',1, '2020-12-22 10:04:07.47829','player', 'complete_chain'),
('toto8','toto_firm8',1,'2020-12-22 09:17:09.93821', 'player', 'complete_chain'),
('toto9','toto_firm9',1, '2020-12-22 10:04:07.47829','player', 'complete_chain'),
('toto10','toto_firm10',1,'2020-12-22 09:17:09.93821', 'player', 'complete_chain'),
('toto11','toto_firm11',1, '2020-12-22 10:04:07.47829','player', 'complete_chain'),
('toto12','toto_firm12',1, '2020-12-22 10:04:07.47829','player', 'complete_chain'),
('toto13','toto_firm13',1,'2020-12-22 09:17:09.93821', 'player', 'complete_chain'),
('toto14','toto_firm14',1, '2020-12-22 10:04:07.47829','player', 'complete_chain'),
('toto15','toto_firm15',1,'2020-12-22 09:17:09.93821', 'player', 'complete_chain');

-- for the tests step 1 and 4 
INSERT INTO actor (generic_name, firm_name, initial_stock, password,type,name_supply_chain) VALUES
('Rose Supplier 1','toto_test1',1, 'pbkdf2:sha256:260000$eLNK8FGJO2kORNgg$3229dee1721a8f711775ee59a46cc5b17c86149c31ef22be5edbde5fb671eb3epbkdf2:sha256:260000$eLNK8FGJO2kORNgg$3229dee1721a8f711775ee59a46cc5b17c86149c31ef22be5edbde5fb671eb3e','player', 'test3'),
('Rose Supplier 2','toto_test2',1, 'pbkdf2:sha256:260000$eLNK8FGJO2kORNgg$3229dee1721a8f711775ee59a46cc5b17c86149c31ef22be5edbde5fb671eb3e','player', 'test3'),
('Magic Capsule Producer','toto_test3',1, 'pbkdf2:sha256:260000$eLNK8FGJO2kORNgg$3229dee1721a8f711775ee59a46cc5b17c86149c31ef22be5edbde5fb671eb3e','player', 'test3'),
('Central Distribution Center','toto_test4',1, 'pbkdf2:sha256:260000$eLNK8FGJO2kORNgg$3229dee1721a8f711775ee59a46cc5b17c86149c31ef22be5edbde5fb671eb3e','player', 'test3'),
('French Wholesaler','toto_test5',1, '2020-12-22 10:04:07.47829','player', 'test3'),
('German Wholesaler','toto_test6',1, '2020-12-22 10:04:07.47829','player', 'test3'),
('French Pharmacy 1','toto_test7',1, '2020-12-22 10:04:07.47829','player', 'test3'),
('French Pharmacy 2','toto_test8',1, '2020-12-22 10:04:07.47829','player', 'test3'),
('German Pharmacy 1','toto_test9',1, '2020-12-22 10:04:07.47829','player', 'test3'),
('German Pharmacy 2','toto_test10',1, '2020-12-22 10:04:07.47829','player', 'test3'),
('Infinite Supplier','',1, '2020-12-22 10:04:07.47829','universal_supplier', 'test3'),
('French Client 1','',1, '2020-12-22 10:04:07.47829','universal_client', 'test3'),
('French Client 2','',1, '2020-12-22 10:04:07.47829','universal_client', 'test3'),
('German Client 1','',1, '2020-12-22 10:04:07.47829','universal_client', 'test3'),
('German Client 2','',1, '2020-12-22 10:04:07.47829','universal_client', 'test3');

INSERT INTO client_supplier (name_client, name_supplier, name_supply_chain, delivery_time, command_time) VALUES
('Rose Supplier 1', 'Infinite Supplier','test3', 1,1),
('Rose Supplier 2', 'Infinite Supplier','test3', 1,1),
('Magic Capsule Producer', 'Rose Supplier 1','test3', 1,1),
('Magic Capsule Producer',  'Rose Supplier 2','test3', 1,1),
('Central Distribution Center', 'Magic Capsule Producer','test3', 1,1),
('French Wholesaler', 'Central Distribution Center','test3', 1,1),
('German Wholesaler', 'Central Distribution Center','test3', 1,1),
('French Pharmacy 1', 'French Wholesaler','test3', 1,1),
('French Pharmacy 2', 'French Wholesaler','test3', 1,1),
('German Pharmacy 1', 'German Wholesaler','test3', 1,1),
('German Pharmacy 2', 'German Wholesaler','test3', 1,1),
('French Client 1', 'French Pharmacy 1','test3', 1,1),
('French Client 2', 'French Pharmacy 2','test3', 1,1),
('German Client 1', 'German Pharmacy 1','test3', 1,1),
('German Client 2', 'German Pharmacy 2','test3', 1,1);

-- Insert command and delivery for checking that step 1 of player is doing correctly

INSERT INTO delivery_command (name_client,name_supplier,name_supply_chain, quantity,seen_by_actor,type,round) VALUES
('Rose Supplier 1', 'Infinite Supplier','test3', 1, false,'command',1),
('Rose Supplier 2', 'Infinite Supplier','test3', 1, false,'command',1),
('Magic Capsule Producer', 'Rose Supplier 1','test3', 1, false,'command',1),
('Magic Capsule Producer',  'Rose Supplier 2','test3', 1, false,'command',1),
('Central Distribution Center', 'Magic Capsule Producer','test3', 1, false,'command',1),
('French Wholesaler', 'Central Distribution Center','test3', 1, false,'command',1),
('German Wholesaler', 'Central Distribution Center','test3', 1, false,'command',1),
('French Pharmacy 1', 'French Wholesaler','test3', 1, false,'command',1),
('French Pharmacy 2', 'French Wholesaler','test3', 1, false,'command',1),
('German Pharmacy 1', 'German Wholesaler','test3', 1, false,'command',1),
('German Pharmacy 2', 'German Wholesaler','test3', 1, false,'command',1),
('French Client 1', 'French Pharmacy 1','test3', 1, false,'command',1),
('French Client 2', 'French Pharmacy 2','test3', 1, false,'command',1),
('German Client 1', 'German Pharmacy 1','test3', 1, false,'command',1),
('German Client 2', 'German Pharmacy 2','test3', 1, false,'command',1);

INSERT INTO delivery_command (name_client,name_supplier,name_supply_chain, quantity,seen_by_actor,type,round) VALUES
('Rose Supplier 1', 'Infinite Supplier','test3', 1, false,'delivery',1),
('Rose Supplier 2', 'Infinite Supplier','test3', 1, false,'delivery',1),
('Magic Capsule Producer', 'Rose Supplier 1','test3', 1, false,'delivery',1),
('Magic Capsule Producer',  'Rose Supplier 2','test3', 1, false,'delivery',1),
('Central Distribution Center', 'Magic Capsule Producer','test3', 1, false,'delivery',1),
('French Wholesaler', 'Central Distribution Center','test3', 1, false,'delivery',1),
('German Wholesaler', 'Central Distribution Center','test3', 1, false,'delivery',1),
('French Pharmacy 1', 'French Wholesaler','test3', 1, false,'delivery',1),
('French Pharmacy 2', 'French Wholesaler','test3', 1, false,'delivery',1),
('German Pharmacy 1', 'German Wholesaler','test3', 1, false,'delivery',1),
('German Pharmacy 2', 'German Wholesaler','test3', 1, false,'delivery',1),
('French Client 1', 'French Pharmacy 1','test3', 1, false,'delivery',1),
('French Client 2', 'French Pharmacy 2','test3', 1, false,'delivery',1),
('German Client 1', 'German Pharmacy 1','test3', 1, false,'delivery',1),
('German Client 2', 'German Pharmacy 2','test3', 1, false,'delivery',1);



--INSERT INTO delivery_command (name_client,name_supplier,name_supply_chain, quantity,seen_by_actor,type) VALUES
--('Central Distribution Center','Magic Capsule Producer','test3',2,false,'command');

INSERT INTO delivery_command (name_client,name_supplier,name_supply_chain, quantity,seen_by_actor,type,round) VALUES
('Rose Supplier 1', 'Infinite Supplier','test3', 1, false,'delivery',0),
('Rose Supplier 2', 'Infinite Supplier','test3', 1, false,'delivery',0),
('Magic Capsule Producer', 'Rose Supplier 1','test3', 1, false,'delivery',0),
('Magic Capsule Producer',  'Rose Supplier 2','test3', 1, false,'delivery',0),
('Central Distribution Center', 'Magic Capsule Producer','test3', 1, false,'delivery',0),
('French Wholesaler', 'Central Distribution Center','test3', 1, false,'delivery',0),
('German Wholesaler', 'Central Distribution Center','test3', 1, false,'delivery',0),
('French Pharmacy 1', 'French Wholesaler','test3', 1, false,'delivery',0),
('French Pharmacy 2', 'French Wholesaler','test3', 1, false,'delivery',0),
('German Pharmacy 1', 'German Wholesaler','test3', 1, false,'delivery',0),
('German Pharmacy 2', 'German Wholesaler','test3', 1, false,'delivery',0),
('French Client 1', 'French Pharmacy 1','test3', 1, false,'delivery',0),
('French Client 2', 'French Pharmacy 2','test3', 1, false,'delivery',0),
('German Client 1', 'German Pharmacy 1','test3', 1, false,'delivery',0),
('German Client 2', 'German Pharmacy 2','test3', 1, false,'delivery',0);

INSERT INTO delivery_command (name_client,name_supplier,name_supply_chain, quantity,seen_by_actor,type,round) VALUES
('Rose Supplier 1', 'Infinite Supplier','test3', 1, false,'command',0),
('Rose Supplier 2', 'Infinite Supplier','test3', 1, false,'command',0),
('Magic Capsule Producer', 'Rose Supplier 1','test3', 1, false,'command',0),
('Magic Capsule Producer',  'Rose Supplier 2','test3', 1, false,'command',0),
('Central Distribution Center', 'Magic Capsule Producer','test3', 1, false,'command',0),
('French Wholesaler', 'Central Distribution Center','test3', 1, false,'command',0),
('German Wholesaler', 'Central Distribution Center','test3', 1, false,'command',0),
('French Pharmacy 1', 'French Wholesaler','test3', 1, false,'command',0),
('French Pharmacy 2', 'French Wholesaler','test3', 1, false,'command',0),
('German Pharmacy 1', 'German Wholesaler','test3', 1, false,'command',0),
('German Pharmacy 2', 'German Wholesaler','test3', 1, false,'command',0),
('French Client 1', 'French Pharmacy 1','test3', 1, false,'command',0),
('French Client 2', 'French Pharmacy 2','test3', 1, false,'command',0),
('German Client 1', 'German Pharmacy 1','test3', 1, false,'command',0),
('German Client 2', 'German Pharmacy 2','test3', 1, false,'command',0);

--INSERT INTO delivery_command (name_client,name_supplier,name_supply_chain, quantity,seen_by_actor,type,round) VALUES
--('Rose Supplier 1', 'Infinite Supplier','test3', 4, false,'command',2),
--('Rose Supplier 2', 'Infinite Supplier','test3', 3, false,'command',2),
--('Magic Capsule Producer', 'Rose Supplier 1','test3', 6, false,'command',2),
--('Magic Capsule Producer',  'Rose Supplier 2','test3', 6, false,'command',2),
--('Central Distribution Center', 'Magic Capsule Producer','test3', 7, false,'command',2),
--('French Wholesaler', 'Central Distribution Center','test3', 7, false,'command',2),
--('German Wholesaler', 'Central Distribution Center','test3', 1, false,'command',2),
--('French Pharmacy 1', 'French Wholesaler','test3', 1, false,'command',2),
--('French Pharmacy 2', 'French Wholesaler','test3', 1, false,'command',2),
--('German Pharmacy 1', 'German Wholesaler','test3', 1, false,'command',2),
--('German Pharmacy 2', 'German Wholesaler','test3', 1, false,'command',2),
--('French Client 1', 'French Pharmacy 1','test3', 1, false,'command',2),
--('French Client 2', 'French Pharmacy 2','test3', 1, false,'command',2),
--('German Client 1', 'German Pharmacy 1','test3', 1, false,'command',2),
--('German Client 2', 'German Pharmacy 2','test3', 1, false,'command',2);
