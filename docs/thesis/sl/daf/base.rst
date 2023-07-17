DAF - *Discord Advertisement Framework*

.. note:: 

    Sledeča vsebina se včasih nanaša na objekte, ki niso podrobno
    opisani v diplomskem delu, so pa na voljo v `uradni spletni dokumentaciji projekta <https://daf.davidhozic.com>`_.


.. figure:: ./DEP/logo.png
    :width: 3cm

    Discord Advertisement Framework logo

    (Narejen z DALL-E & Adobe Photoshop)


Namen projekta
=================
Pobudo za projekt sem prejel od kolega,
ki je za svoj projekt povezan z nezamenljivimi žetoni potreboval orodje, ki bi po več dni v tednu lahko
neprestano samodejno oglaševalo njegov projekt po različnih cehih.

Cilj projekta je izdelati ogrodje, ki lahko deluje 24 ur na dan in samodejno oglašuje v naprej definirano vsebino ali
pa tudi dinamično vsebino, omogoča pregled poslanih sporočil in poročanje o uspešnosti preko beleženja zgodovine
poslanih sporočil.
Ker naj bi to ogrodje delovalo brez prekinitev je cilj ogrodje narediti, da bo delovalo kot demonski proces v ozadju
brez grafičnega vmesnika. Ker je pa definicija brez grafičnega vmesnika težja in zahteva malo več dela, je cilj izdelati
tudi grafični vmesnik, ki bo deloval kot dodaten nivo nad samim ogrodjem ter omogočal :ref:`generacijo oglaševalske skripte <Pošiljanje sporočila z naključno periodo>`, 
ki se jo lahko potem zažene na strežniku brez grafičnega vmesnika za neprekinjeno oglaševanje. Za lažji pregled dogajanja
na strežniku, je cilj na grafičnem vmesniku implementirati možnost oddaljenega dostopa, ki bo omogočal direktno manipulacijo
oglaševalske sheme in pregled zgodovine poslanih sporočil za določitev uspešnosti oglaševanja.
