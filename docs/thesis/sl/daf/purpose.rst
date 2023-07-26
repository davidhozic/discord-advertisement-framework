
Namen projekta
=================
Pobuda za projekt diplomske naloge je bila podana s strani kolega, ki je za svoj projekt, povezan z
nezamenljivimi žetoni, potreboval orodje, ki bi po več dni v tednu lahko neprestano samodejno oglaševalo njegov projekt po različnih cehih.


.. figure:: ./DEP/logo.png
    :height: 5cm
    :align: center

    Logotip projekta (Narejen z DALL-E & Adobe Photoshop)


Cilj projekta je izdelati ogrodje, ki lahko deluje 24 ur na dan in samodejno oglašuje v naprej definirano vsebino ali
pa tudi dinamično vsebino, omogoča pregled poslanih sporočil in poročanje o uspešnosti preko beleženja zgodovine
poslanih sporočil.
Ker naj bi ogrodje delovalo brez prekinitev je cilj ogrodje izdelati na način, da bo delovalo kot demonski proces v ozadju
brez grafičnega vmesnika.

Konfiguracijo ogrodja se bo izvedlo preko Python datoteke oz. skripte, katero se bo potem neposredno pognalo
v Python okolju. Ker ta način konfiguracije zahteva nekaj dela in ni najbolj enostaven, je cilj izdelati
tudi grafični vmesnik, ki bo deloval kot dodaten nivo nad samim jedrom ogrodja, ter omogočal konfiguracijo in izvoz konfiguracije
na način, da se bo le to lahko uporabilo brez grafičnega vmesnika.

Za lažji pregled dogajanja na strežniku, je cilj na grafičnem vmesniku implementirati možnost oddaljenega dostopa,
ki bo omogočal direktno manipulacijo s sporočili in pregled zgodovine poslanih sporočil za določitev uspešnosti oglaševanja.
