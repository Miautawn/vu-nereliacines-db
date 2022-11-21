CREATE 

// modeling entities
(jonas:USER{name:"Jonas", surname: "Jonaitis" , age: 33}),
(juozas:USER{name:"Juozas", surname: "Juozaitis", age: 23}),
(ruta:USER{name:"Ruta", surname: "Rutaite", age: 41}),
(monika:USER{name:"Monika", surname: "Monikaite", age: 14}),

(jonas_post_1:POST{UUID: "POST1", title: "Kokia didele pagavau!", description: "Kauno mariose pagavau :)"}),
(jonas_post_2:POST{UUID: "POST2", title: "Nesigavo siandien", description: "Nieko nepagavau :("}),
(juozas_post_1:POST{UUID: "POST3", title: "Vokes grobis", description: "Labai sekminga diena buvo prie vokes!"}),
(monika_post_1:POST{UUID: "POST4", title: "Pirma zvejybos diena!", description: "Pirmoji keliones diena buvo labai gera"}),
(monika_post_2:POST{UUID: "POST5", title: "Antra zvejybos diena!", description: "Antroji keliones diena buvo prasta"}),
(monika_post_3:POST{UUID: "POST6", title: "Trecia zvejybos diena!", description: "Nebenoriu zvejoti :("}),

// modelling relationships
(jonas) -[:FRIENDS]-> (juozas),
(juozas) -[:FRIENDS]-> (ruta),
(juozas) -[:FRIENDS]-> (monika),
(ruta) -[:FRIENDS]-> (monika),

(jonas) -[:POSTED]-> (jonas_post_1),
(jonas) -[:POSTED]-> (jonas_post_2),
(juozas) -[:POSTED]-> (juozas_post_1),
(monika) -[:POSTED]-> (monika_post_1),
(monika) -[:POSTED]-> (monika_post_2),
(monika) -[:POSTED]-> (monika_post_3),

(jonas) -[:LIKES]-> (juozas_post_1),
(monika) -[:LIKES]-> (juozas_post_1),
(juozas) -[:LIKES]-> (monika_post_2),
(ruta) -[:LIKES]-> (monika_post_1),
(ruta) -[:LIKES]-> (monika_post_2),
(ruta) -[:LIKES]-> (monika_post_3);