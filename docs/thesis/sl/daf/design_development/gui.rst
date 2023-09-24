

============================================
Zasnova in razvoj grafičnega vmesnika
============================================

Ogrodje lahko v celoti deluje brez grafičnega vmesnika, a ta način zahteva pisanje konfiguracijskih ``.py`` datotek
oz. Python skript, kar je marsikomu težje, sploh če se še nikoli niso srečali s Python jezikom.

V namen enostavnejše rabe ogrodja je izdelan grafični vmesnik, ki deluje ločeno od samega jedra ogrodja, z njim pa
lahko komunicira lokalno preko programskega vmesnika ali pa na daljavo preko HTTP vmesnika.

Za dizajn vmesnika je izbran svetel dizajn, z modrimi odtenki za posamezne elemente (:numref:`fig-gui-front`).



Tkinter
=============================
Za izdelavo grafičnega vmesnika je bila uporabljena knjižnica `ttkboostrap <https://ttkbootstrap.readthedocs.io/en/latest/>`_, ki je razširitev
vgrajene Python knjižnice :mod:`tkinter`.

Tkinter knjižnica je v osnovi vmesnik na Tcl/Tk orodje za izdelavo grafičnih vmesnikov, doda pa tudi nekaj svojih nivojev,
ki še dodatno razširijo delovanje knjižnice.
Omogoča definicijo različnih pripomočkov (angl. *widgets*), ki se jih da dodatno razširiti in shraniti pod nove
pripomočke, ki jih lahko večkrat uporabimo. Ti pripomočki so na primer :class:`~tkinter.ttk.Combobox`, ki je neke vrste 
(angl.) "drop-down" meni, :class:`~tkinter.ttk.Spinbox` za vnašanje številskih vrednosti, :class:`~tkinter.ttk.Button` za gumbe ipd.
Posamezne pripomočke se da tudi znatno konfigurirati, kjer lahko spreminjamo stile, velikost, pisavo ipd :ref:`tkinter_py_docs`.

Pred izbiro Tkinter knjižnice je bila ena izmed možnosti tudi knjižnica PySide (QT), a na koncu se je vseeno obnesla Tkinter
oz. ttkboostrap knjižnica, saj je že osnovni paket PySide6 knjižnice velik 70 MB, z dodatki pa skoraj 200 MB, medtem ko je Tkinter
na veliko platformah že prisotna kar v sami Python distribuciji in ne zahteva nobene dodatne namestitve, torej je
ttkboostrap edina dodatna zunanja knjižnica, ki jo je potrebno namestiti, in sicer se namesti kar sama, ob prvem zagonu grafičnega
vmesnika.


Zavihki
=============================
Grafični vmesnik ogrodja je razdeljen na več zavihkov, kjer je vsak namenjen ločenim funkcionalnostim.


*Optional modules* zavihek
-----------------------------
*Optional modules* zavihek omogoča namestitev dodatnih modulov, ki jih osnovni paket ogrodja pogreša (zaradi hitrejšega zagona).
Sestavljen je iz statusnih panelov, ki v primeru, da so obarvani rdeče (modul ni nameščen), vsebujejo še gumb za namestitev.
Gumb bo namestil potrebne pakete, potem pa bo uporabniku sporočeno, da mora za spremembe ponovno odpreti vmesnik.
Po ponovnem zagonu bo statusni panel za posamezen modul obarvan zeleno.

.. figure:: ./DEP/daf-gui-modules-tab.png

    Izgled *Optional Modules* zavihka


*Schema definition* zavihek
-----------------------------
*Schema definition* omogoča definicijo uporabniških računov (in v njih cehov, sporočil ipd.), definicijo upravljalnika za beleženje,
izbiro globine izpisov na konzoli in konfiguracijo povezave do jedra ogrodja.
Omogoča tudi shrambo teh definicij v JSON datoteko, branje definicij iz JSON datoteke in generacijo ekvivalentne
Python datoteke (konfiguracijske datoteke jedra), ki požene le jedro orodja (brez grafičnega vmesnika).
Pravzaprav je ta zavihek namenjen definiciji neke predloge, ki jo lahko potem uvozimo v jedro ogrodja.
Izgled je prikazan na :numref:`fig-gui-front`.

Omogoča tudi dinamično branje in dodajanje objektov v že zagnanem vmesniku preko gumbov, ki vsebujejo besedo *live*.

Uporabniške račune (in ostale objekte) se lahko definira s klikom na opcijski meni *Object options* in opcijo *New ACCOUNT*.
Ob kliku se odpre novo okno, ki je avtomatično in dinamično generirano iz podatkov o podatkovnih tipih, ki jih sprejme
razred ob definiciji. Za vsak parameter se generirajo oznaka, opcijski meni in opcijski gumb, v katerem lahko urejamo izbrano vrednost
oz. definiramo novo.

.. figure:: ./DEP/images/gui-new-item-define.png
    :height: 8cm
    :align: center

    Definicija uporabiškega računa

Shranjevanje sheme (predloge) v datoteko, nalaganje sheme iz datoteke in generiranje ekvivalentne Python datoteke
je možno preko opcijskega menija *Schema*. Datoteka, kamor se shrani shema, je datoteka formata JSON in vsebuje
definirane račune, objekte za beleženje sporočil, objekte za povezovanje z jedrom ipd.
Vsi objekti znotraj grafičnega vmesnika pravzaprav niso pravi Python objekti, ampak so dodaten nivo abstrakcije, ki je sestavljen
iz samega podatkovnega tipa (razreda) definiranega objekta in pa parametrov, ki so shranjeni pod slovar (:class:`dict`).
Pretvorba v JSON poteka rekurzivno, tako da se za vsak objekt v JSON naredi nov pod-slovar, kjer so zapisani
podatkovni tip (kot besedilo) in parametri objekta.

Nalaganje sheme (predloge) iz JSON datoteke je možno preko *Schema* menija in poteka rekurzivno, tako da se za vsak vnos najprej na podlagi celotne poti
do razreda naloži (angl. *import*) Python modul, potem pa iz modula še podatkovni tip (razred). Zatem se
ustvari abstraktni objekt na enak način, kot je bil ustvarjen pred shranjevanjem v JSON shemo.    

Preko *Schema* menija je možno ustvariti tudi ekvivalentno Python datoteko, ki bo oglaševala na enak način kot v grafičnem vmesniku, brez
dejanskega grafičnega vmesnika. Ob kliku na gumb *Generate script* se definira Python koda, ki na vrhu
definira vse potrebno in zatem zažene ogrodje. Primer skripte je prikazan v :numref:`example-text-message-randomized-period`.


*Live view* zavihek
-----------------------------
Medtem ko je :ref:`*Schema definition* zavihek` namenjen definiciji vnaprej definirane sheme oz. predloge objektov,
*Live view* zavihek omogoča direktno manipulacijo z objekti, ki so dodani v delujoče jedro ogrodja.

Na začetku zavihka se nahaja opcijski meni, v katerem je *add_object* funkcija, znotraj katere lahko definiramo nov račun.
Ob kliku na gumb *Execute* bo definiran račun takoj dodan v ogrodje in začel z oglaševanjem.

Pod opcijskim menijem se nahajajo trije gumbi. *Refresh* posodobi spodnji seznam z uporabniškimi računi, ki oglašujejo, *Edit*
gumb odpre okno za definiranje računov, kjer se vanj naložijo obstoječe vrednosti iz uporabniškega računa, ki ga urejamo.
Okno poleg gumbov oz. pripomočkov, ki jih ima pri urejanju v :ref:`Schema definition zavihku <*Schema definition* zavihek>`, vsebuje
tudi dva dodatna gumba. Ta gumba sta *Refresh* gumb, ki v okno naloži osvežene vrednosti iz dejanskega objekta, dodanega v ogrodje, in 
*Live update* gumb, ki dejanski objekt v ogrodju na novo inicializira z vrednostmi, definiranimi v oknu. Na dnu okna je znotraj
vijoličnega okvirja možno izvajanje metod (funkcij) na objektu.

.. figure:: ./DEP/images/gui-live-view-edit-account.png
    :width: 10cm

    Prikaz parametrov in metod delujočega računa


.. figure:: ./DEP/daf-gui-live-view.png

    *Live view* zavihek



*Output* zavihek
-----------------------------
Vse, kar se nahaja v *Output* zavihku, je seznam izpisov, ki se izpišejo na standardnem izhodu STDOUT.
Uporabi se ga lahko za bolj podroben pregled, kaj se dogaja z jedrom ogrodja.

.. figure:: ./DEP/daf-gui-output-tab.png

    *Output tab* zavihek


*Analytics* zavihek
-----------------------------
*Analytics* zavihek omogoča analizo poslanih sporočil in njihovo statistiko. Prav tako omogoča analizo pridruževanj preko sledenja
cehovskih pridružnih povezav (angl. *Invite links*). Izgled je prikazan na :numref:`daf-gui-analytics-tab-rotated`.

Za pridobitev vnosov se uporabi gumb *Get logs*, ki na podlagi parametrov, definiranih v zgornjem opcijskem meniju, vrne
v spodnji seznam filtrirane elemente. Te elemente se lahko vsakega posebej pregleda z gumbom *View log*, ki 
odpre okno za urejanje objektov.

Za pridobitev statistike se uporabi gumb *Calculate*, ki na podlagi opcijskega menija nad gumbom v spodnjo tabelo vrne podatke.


.. figure:: ./DEP/images/gui-analytics-message-frame-view-log.png
    :height: 8cm

    Prikaz vnosa o poslanem sporočilu.


Povezava grafičnega vmesnika z jedrom ogrodja
=====================================================
Grafični vmesnik lahko s stališča lokacije delovanja deluje na dva načina. Prvi je lokalni način, kjer grafični vmesnik
jedro ogrodja zažene na istem računalniku. Drugi način je oddaljeni režim delovanja,
kjer se grafični vmesnik poveže na HTTP strežnik, ki deluje znotraj jedra ogrodja, in nanj
pošilja zahtevke, ki se v jedru potem preslikajo na programski vmesnik. Koncept je prikazan na :numref:`gui-core-connection`.

V primeru oddaljenega dostopa se podatki serializirajo v JSON reprezentacijo, kjer so navadne vrednosti neposredno serializirane v JSON format,
večina objektov pa v slovar (:class:`dict`), kjer so zapisani pot do podatkovnega tipa (razreda) objekta in njegovi atributi.
Obstaja nekaj izjem pri serializaciji objektov, ena izmed teh je :class:`~datetime.datetime` tip objekta, ki se serializira v besedilo po standardu ISO 8601.
Pretvorbo v končno JSON reprezentacijo opravlja vgrajena knjižnica :mod:`json`, medtem ko pretvorbo objektov v slovar
opravlja funkcija :func:`daf.convert.convert_object_to_semi_dict`. Serializacijo in deserializacijo opravljata grafični vmesnik in
jedro oba enako. Včasih se pri pošiljanju podatkov iz grafičnega vmesnika na jedro sploh ne serializira,
temveč se pošlje le referenco (identifikator) objekta, kjer se na strežniku (jedru) objekt pridobi iz spomina preko reference. 

.. autofunction:: daf.convert.convert_object_to_semi_dict

Za konfiguracijo oddaljenega dostopa je potrebno na vrhu vmesnika izbrati :class:`~daf_gui.connector.RemoteConnectionCLIENT`
in nastaviti parametre. Prav tako je potrebno ustrezno konfigurirati jedro [#extra_remote_conf]_.

.. [#extra_remote_conf] Več o konfiguraciji je na voljo v dokumentaciji ogrodja - :ref:`Remote control (core)`.
