.. raw:: latex

    \newpage

============================================
Zasnova in razvoj grafičnega vmesnika
============================================

.. _Python: https://www.python.org

DAF lahko deluje samostojno popolnoma brez grafičnega vmesnika, a ta način zahteva pisanje *.py* datotek oz. Python skript, kar
je marskikomu težje, sploh če se še nikoli niso srečali s Python jezikom.

V namen enostavnejše rabe ogrodja je izdelan grafični vmesnik, ki deluje ločeno od samega jedra ogrodja, z njim pa
lahko komunicira lokalno preko programskega vmesnika ali pa na daljavo preko HTTP vmesnika.

Za dizajn vmesnika je izbran svetel dizajn, z modrimi odtenki za posamezne elemente, kot je to prikazano na :numref:`sliki %s <fig-gui-front>`.

.. _fig-gui-front:
.. figure:: ./DEP/daf-gui-front-rotated.png
    :height: 20.5cm

    Grafični vmesnik (*Schema definition* zavihek)


.. raw:: latex

    \newpage


Tkinter
=============================
Za izdelavo grafičnega vmesnika je bila uporabljena knjižnica `ttkboostrap <https://ttkbootstrap.readthedocs.io/en/latest/>`_, ki je razširitev
vgrajene Python_ knjižnice :mod:`tkinter`.

Tkinter knjižnica je v osnovi vmesnik na Tcl/Tk orodja za izdelavo grafičnih vmesnikov, doda pa tudi nekaj svojih nivojev,
ki še dodatno razširijo delovanje knjižnice.
Omogoča definicijo različnih pripomočkov (angl. *widgets*), ki se jih da dodatno razširiti in shraniti pod nove
pripomočke, katere lahko večkrat uporabimo. Ti pripomočki so na primer :class:`~tkinter.ttk.Combobox`, ki je neke vrste 
(angl.) "drop-down" meni, :class:`~tkinter.ttk.Spinbox` za vnašanje številskih vrednosti, gumbi :class:`~tkinter.ttk.Button`, itd.
Posamezne pripomočke se da tudi znatno konfigurirati, kjer lahko spreminjamo stile, velikost, pisavo, ipd.
Več o Tkinter knjižnici si lahko preberete :mod:`na uradni Python dokumentaciji <tkinter>`.

Pred izbiro Tkinter knjižnice je bila ena izmed možnosti tudi knjižnica PySide (QT), a na koncu se je vseeno obnesla Tkinter
oz. ttkboostrap knjižnica, saj je že osnovni paket PySide6 knjižnice velik 70 MB, z dodatki pa skoraj 200 MB, medtem ko je Tkinter
na veliko platformah že pristona kar v sami Python distribuciji in ne zahteva nobene dodatne namestitve, torej je
ttkboostrap edina dodatna zunanja knjižnica, ki jo je potrebno namesti, in sicer se namesti kar sama ob prvem zagonu grafičnega
vmesnika.


Zavihki
=============================
Grafični vmesnik DAF je razdeljen na več zavihkov, kjer je vsak namenjen ločenim funkcionalnostim.


*Optional modules* zavihek
-----------------------------
*Optional modules* zavihek omogoča namestitev dodatnih modulov, ki v osnovem DAF paketu niso prisotni (zaradi hitrejšega zagona).
Sestavljen je iz statusnih panelov, ki če so rdeči (modul ni nameščen) vsebuje še gumb za namestitev.
Gumb bo namestil potrebne pakete, potem pa bo uporabniku sporočeno, da mora za spremembe ponovno odpreti vmesnik.
Po ponovnem zagonu bo statusni panel za posamezen modul obarvan zeleno.

.. figure:: ./DEP/daf-gui-modules-tab.png

    Izgled *Optional Modules* zavihka


.. raw:: latex

    \newpage



*Schema definition* zavihek
-----------------------------
*Schema definition* omogoča definicijo uporabniških računov (in v njih cehov, sporočil, ...), definicijo upravljalnika za beleženje,
izbiro globine izpisov na konzoli in konfiguracijo povezave do jedra ogrodja.
Omogoča tudi shrambo teh definicij v :term:`JSON` datoteko, braje definicij iz JSON datoteke in pa generacijo ekvivalentne
Python datoteke, ki požene le :ref:`jedro orodja <Zasnova in razvoj jedra>` (brez grafičnega vmesnika).
Pravzaprav je ta zavihek namenjen definiciji nekege predloge, ki jo lahko potem uvozimo v jedro ogrodja.
Izgled je prikazan na :numref:`sliki %s <fig-gui-front>`.

Omogoča tudi dinamično branje in pretvorbo objektov v že zagnanem vmesniku preko gumbov, ki vsebujejo besedo *live*.

Uporabniške račune (in ostale objekte) se lahko definira z klikom na opcijski meni *Object options*, in opcijo *New ACCOUNT*.
Ob kliku se odpre novo okno, ki je avtomatično in dinamično generirano iz podatkov o podatkovnih tipih (anotacij), ki jih sprejme
razred ob definiciji. Za vsak parameter se generirajo labela, opcijski meni in opcijski gumb, v katerem lahko urejamo izbrano vrednost
oz. definiramo novo vrednost. 

.. figure:: ./DEP/images/gui-new-item-define.png
    :height: 8cm
    :align: center

    Definicija uporabiškega računa

Shranjevanje sheme (predloge) v datoteko in nalaganje sheme iz datoteke in generiranje ekvivalentne Python_ datoteke
je možno preko opcijskega menija *Schema*. Datoteka, kamor se shrani shema je datoteka formata JSON in vsebuje
definirane račune, objekte za beleženje sporočil, objekte za povezovanje z jedrom ipd.
Vsi objekti znotaj grafičnega vmesnika, pravzaprav niso pravi Python objekti ampak so dodaten nivo abstrakcije, ki je sestavljen
iz samega podatkovnega tipa (razreda) definiranega objekta in pa parametrov, ki so shanjeni pod slovar (:class:`dict`).
Pretvorba v JSON poteka rekurzivno tako, da se za vsak objekt, v JSON naredi nov podslovar, kjer sta noter zapisana
podatkovni tip (kot besedilo) in pa parametri objekta.

Nalaganje sheme (predloge) iz JSON datoteke je možno preko *Schema* menija in poteka rekurzivno tako, da se za vsak vnos najprej na podlagi celotne poti
do razreda naloži (angl. *import*) Python modul, potem pa iz modula še podatkovni tip (razred). Za tem se
ustvari abstraktni objekt na enak način kot je bil ustvarjen pred shranjevanjem v JSON shemo.    

Preko *Schema* menija je možno ustvariti tudi ekvavilentno Python datoteko, ki bo oglaševala na enak način kot v grafičnem vmesniku, brez
dejanskega grafičnega vmesnika. Ob kliku na gumb *Generate script* se definira Python koda, ki na vrhu
definira vse potrebno in zatem zažene ogrodje. Primer skripte je prikazan v :numref:`example-text-message-randomized-period`.


.. raw:: latex

    \newpage


*Live view* zavihek
-----------------------------
Medtem, ko je :ref:`*Schema definition* zavihek` namenjen definiciji v naprej definirane sheme oz. predloge objektov,
*Live view* zavihek omogoča direktno manipulacijo z objekti, ki so dodani v delujoče jedro ogrodja.

Na začetku zavihka se nahaja opcijski meni, v katerem je *add_object* funkcija, kateri znotraj lahko definiramo nov račun.
Ob kliku na gumb *Execute* bo definiran račun takoj dodan v DAF in začel z oglaševanjem.

Pod opcijskem menijem se nahajajo 3 gumbi. *Refresh* posodobi spodnji seznam z računi, ki oglašujejo v DAF, *Edit*
gumb odpre okno za definiranje računov, kjer se vanj naložijo obstoječe vrednosti iz uporabniškega računa, ki ga urejamo.
Okno poleg gumbov oz. pripomočkov, ki jih ima pri urejanju v :ref:`Schema definition zavihku <*Schema definition* zavihek>`, vsebuje
tudi 2 dodatna gumba. Ta gumba sta *Refresh* gumb, ki v okno naloži osvežene vrednosti iz dejanskega objekta dodanega v DAF in 
*Live update* gumb, ki dejanski objekt v DAF, na novo inicializira z vrednostnimi definiranimi v oknu. Na dnu okna je znotraj
vijoličnega okvirja možno izvajanje metod (funkcij) na objektu.

.. figure:: ./DEP/images/gui-live-view-edit-account.png
    :width: 10cm

    Prikaz parametrov in metod delujočega računa


.. figure:: ./DEP/daf-gui-live-view.png

    *Live view* zavihek


.. raw:: latex

    \newpage



*Output* zavihek
-----------------------------
Vse kar se nahaja v *Output* zavihku, je seznam izpisov, ki se izpišejo na standardnem izhodu STDOUT.
Uporabi se ga lahko za bolj podroben pregled kaj se dogaja z jedrom DAF.

.. figure:: ./DEP/daf-gui-output-tab.png

    *Output tab* zavihek


.. raw:: latex

    \newpage


*Analytics* zavihek
-----------------------------
*Analytics* zavihek omogoča analizo poslanih sporočil in njihovo statistiko. Prav tako omogoča analizo pridruževanj preko sledenja
cehovskih povezav (angl. *Invite links*).

Za pridobitev vnosov, se uporabi gumb *Get logs*, ki na podlagi parametrov definiranih v zgornjem opcijskem meniju, vrne
v spodnji seznam filtrirane elemente. Te elemente se lahko vsakega posebej pregleda z gumbom *View log*, ki 
odpre okno za urejanje objektov.

Za pridobitev statistike se uporabi gumb *Calculate*, ki na podlagi opcijskega meniji nad gumbom, v spodnjo tabelo vrne podatke.


.. figure:: ./DEP/images/gui-analytics-message-frame-view-log.png
    :height: 8cm

    Prikaz vnosa o poslanem sporočilu.


.. figure:: ./DEP/daf-gui-analytics-tab-rotated.png
    :height: 20.5cm

    Zavihek *Analytics*


.. raw:: latex

    \newpage


Povezava grafičnega vmesnika z jedrom ogrodja
=====================================================
Grafični vmesnik lahko s stališča lokacije delovanja deluje na dva načina. Prvi je lokalen način, kjer grafični vmesnik
jedro ogrodja zažene na istem računalniku, kjer deluje grafični vmesnik. Drugi način pa je oddaljen
režim delovanja, kjer se grafični vmesnik poveže na HTTP strežnik, kateri deluje znotraj jedra ogrodja in na ta strežnik
pošilja HTTP ukaze, ki se v jedru mapirajo na programski vmesnik. Koncept je prikazan na :numref:`sliki %s <gui-core-connection>`

V primeru oddaljenega dostopa se podatki serializirajo v :term:`JSON` reprezentacijo, kjer so navadne vrednosti neposredno serializirane v JSON format,
večina objektov pa v slovar (:class:`dict`), kjer je sta slovarju zapisana pot do podatkovnega tipa (razreda) objekta in njegovi attributi.
Obstaja nekaj izjem pri serializaciji objektov, kjer je ena izmed teh :class:`~datetime.datetime` tip objekta, ki se serializira v besedilo po standardu ISO 8601.
Pretvorbo v končno JSON reprezentacijo opravlja vgrajena knjižnica :mod:`json`, medtem ko pretvorbo objektov v slovar
opravlja funkcija :func:`daf.convert.convert_object_to_semi_dict`. Serializacijo in deserializacijo opravljata grafični vmesnik in
jedro oba enako. Včasih se pri pošiljanju podatkov iz grafičnega vmesnika na jedro sploh ne serializira (kot objekte),
temveč se pošlje le referenco (identifikator) objekta, kjer se na strežniku (jedru DAF) objekt pridobi iz spomina prek reference. 

.. autofunction:: daf.convert.convert_object_to_semi_dict

Za konfiguracijo oddaljenega dostopa je potrebno na vrhu vmesnika izbrati :class:`~daf_gui.connector.RemoteConnectionCLIENT`
in nastaviti parametre. Prav tako je potrebno ustrezno konfigurirati jedro. Več o konfiguraciji je na voljo v
:ref:`dokumentaciji ogrodja <Remote control (GUI)>`.

