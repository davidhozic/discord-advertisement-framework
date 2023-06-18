============================================
Zasnova in razvoj grafičnega vmesnika
============================================

.. _Python: https://www.python.org

DAF lahko deluje popolnoma brez grafičnega vmesnika, a ta način zahteva pisanje *.py* datotek oz. Python skript, kar
ja marskikomu težje, sploh če se še nikoli niso srečali s Python jezikom.

V namen enostavnejše izkušnje pri uporabi ogrodja, obstaja grafični vmesnik, ki deluje ločeno od samega ogrodja, z njim pa
lahko komunicira lokalno preko programskega vmesnika ali pa na daljavo preko HTTP vmesnika.

.. figure:: ./DEP/daf-gui-front.png
    :width: 15cm

    Grafični vmesnik (privzet prikaz)

.. raw:: latex

    \newpage

Kot je razvidno iz gornje slike, je za dizajn vmesnika izbran svetel dizajn z modrimi odtenki za posamezne elemente.
Pred to temo je bila planira tema z turkiznimi barvami, vendar je ob odzivih uporabnikov trenuten dizajn bolj obnesel.


Tkinter
------------------
Za izdelavo grafičnega vmesnika je bila uporabljena knjižnica `ttkboostrap <https://ttkbootstrap.readthedocs.io/en/latest/>`_, ki je razširitev
vgrajene Python_ knjižnice :mod:`tkinter`.

Tkinter knjižnica je v osnovi vmesnik na Tcl/Tk orodja za izdelavo grafičnih vmesnikov, doda pa tudi nekaj svojih nivojev,
ki še dodatno razširijo delovanje knjižnice.

Tkinter omogoča definicijo različnih pripomočkov (angl. *widgets*), ki se jih da dodatno razširiti in shraniti pod nove
pripomočke, katere lahko večkrat uporabimo. Ti pripomočki so na primer :class:`ttk.Combobox`, ki je neke vrste 
(angl.) "drop-down" meni, :class:`ttk.Spinbox` za vnašanje številkških vrednosti, gumbi :class:`ttk.Button`, itd.
Posamezne pripomočke se da tudi znatno konfigurirati, kjer lahko spreminjamo stile, velikost, pisavo, ipd.

Več o Tkinter knjižnici si lahko preberete :mod:`na uradni Python dokumentaciji <tkinter>`.

Pred izbiro te knjižnice je bila ena izmed možnosti tudi knjižnica PySide (QT), a na koncu je bila vseeno obnesla Tkinter
oz. ttkboostrap knjižnica, saj je že osnovni paket PySide6 knjižnice velik 70 MB, z dodatki pa skoraj 200 MB, medtem ko je Tkinter
na veliko platformah že pristona kar v sami Python distribuciji in ne zahteva nobene dodatne namestitve, torej je
ttkboostrap edina dodatna zunanja knjižnica, ki jo je potrebno namesti, in sicer se namesti kar sama ob prvem zagonu grafičnega
vmesnika.


Zavihki
----------------------
Grafični vmesnik DAF je razdeljen na več zavihkov, kjer je vsak namenjen ločenim funkcionalnostim.


*Optional modules* zavihek
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Ta zavihek omogoča namestitev dodatnih funkcionalnosti, ki v osnovem DAF paketu niso prisotni (za hitrejši zagon in namestitveni čas).
Sestavljen je iz statusnih panelov, ki če so rdeči (modul ni nameščen) vsebuje še gumb za namestitev.
Gumb bo namestil potrebne pakete, potem pa bo vmesnik uporabniku sporočil, da mora za spremembe ponovno odpreti vmesnik.
Ob ponovnem odprtju po namestitvi bo statusni panel za posamezen modul obarvan zelen.

V prihodnosti je ena izmed možnosti ta, da se grafični vmesnik zapakira v binaren paket. V tem primeru tega zavihka ne bo,
saj se ti paketi namestijo na Python nivoju in ne znotraj DAF ogrodja.


.. figure:: ./DEP/images/gui-depend-install.png
    :width: 15cm

    Zavihek za namestitev dodatnih functionalnosti


*Schema definition* zavihek
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Zavihek omogoča definicijo uporabniških računov (in v njih cehov, sporočil, ...), definicijo upravljalnika za beleženje.
Omogoča tudi shrambo teh definicij v JSON datoteko, braje definicij iz JSON datoteke in pa generacijo ekvivalentne
*.py* datoteke, ki deluje v samem jedru DAF (brez grafičnega vmesnika - :ref:`Zasnova in razvoj jedra`).
Pravzaprav je ta zavihek namenjen definiciji nekege predloge, ki jo lahko potem uvozimo v jedro ogrodja.

.. figure:: ./DEP/images/gui-schema-restore-bnt.png
    :width: 15cm

    Zavihek za definicijo sheme

Omogoča tudi dinamično branje in pretvorbo objektov v že zagnanem vmesniku preko gumbov, ki vsebujejo besedo *live*.

Uporabniške račune (in ostale objekte) se lahko definira z klikom na opcijski meni *Object options*, in opcijo *New ACCOUNT*.
Ob kliku se odpre novo okno, ki je avtomatično in dinamično generirano iz podatkov o podatkovnih tipih (anotacij), ki jih sprejme
razred ob definiciji. Za vsak parameter generira labela, opcijski meni in opcijski gumb, v katerem lahko urejamo izbrano vrednost
oz. definiramo novo vrednost. 

.. figure:: ./DEP/images/gui-new-item-define.png

    Definicija uporabiškega računa

Imel sem veliko srečo, da sem si za izdelavo te aplikacije že na začetku izbral ravno jezik Python_, saj ta jezik omoča dinamično preverjanje in
spreminjanje podatkovnih tipov posameznih spremenljivk oz. atributov (dejansko se menjajo reference na objekte), brez česar bi bila avtomatična generacija definicijskega
okna precej težja, če ne skoraj nemogoča brez da bi se strukturo za posamezne podatkovne tipe nekje (morda v JSON datoteki) ročno
definiralo. Python ima namreč v :mod:`typing` modulu, oz. že neposredno v jezku, vgrajene funkcije za dinamično preverjanje,
manipulacijo in disekcijo podatkovnih tipov.

Uporaba novega okna ni bila planirana od samega začetka, in sicer je bilo v načrtu izdelati nek manjši okvir znotraj glavnega okna,
ki bi v neki drevesni strukturi prikazoval definirane objekte, v nekakšnem slovarnem formatu kot je JSON, a je bilo kmalu
razvidno da bi bilo to težko izdelati, saj ni na voljo nobenega vgrajenega pripomočka ki bi to dopuščal (vsaj ne ključ-vrednost formatu).

Podobno se definira tudi upravljalnik za beleženje.
Pod izbiro za upravljalnik se nahaja tudi opcijski meni za izbiro nivoja izpisov v *Output* zavihku.

Shranjevanje sheme (predloge) v datoteko in nalaganje sheme iz datoteke in generacija ekvivalentne Python_ datoteke
je možno preko opcijskega menija *Schema*. Datoteka, kamor se shrani shema je datoteka formata JSON in vsebuje
definirane račune, beležne upravljalnike, objekte za povezovanje z jedrom ipd.
Vsi objekti znotaj grafičnega vmesnika, pravzaprav niso pravi Python objekti ampak so dodaten nivo abstrakcije, ki je sestavljen
iz samega podatkovnega tipa (razreda) definiranega objekta in pa parametrov, ki so shanjeni pod slovar (:class:`dict`).
Pretvorba v JSON poteka rekurzivno tako da se za vsak objekt v JSON naredi nov pod slovar, kjer je shranjen (kot besedilo)
podatkovni tip in pa parametri, ki so že v slovarnem formatu in se preprosto le prepišejo v JSON datoteko.

.. literalinclude:: ./DEP/example_schema.json
    :caption: Primer JSON sheme

Nalaganje sheme (predloge) iz JSON datoteke je možno preko *Schema* menija in poteka rekurzivno tako, da se za vsak vnos najprej na podlagi celotne poti
do razrade (napisana v besedilu) naloži Python modul, potem pa iz modula še podatkovni tip (razred). Za tem se
ustvari abstraktni objekt na enak način kot je bil ustvarjen pred shranjevanjem v JSON shemo.    

Preko *Schema* menija je možno ustvariti tudi ekvavilentno Python datoteko, ki bo oglaševala na enak način kot v grafičnem vmesniku, brez
dejanskega grafičnega vmesnika. On kliku na gumb *Generate script* se definira Python koda, ki na vrhu vključi vse potrebne
razrede in funkcije, potem se definira upravljalnik za beleženje. Če je bila izbrana opcija oddaljenega dostopa, se zatem
definira še objekt za oddaljen dostop in zatem se definira še tabela uporabniških računov. Na koncu se vse skupaj požene
z funckijo :class:`~daf.core.run`.

.. literalinclude:: ./DEP/shill-script-example.py
    :caption: Primer ekvivalentne Python datoteke


*Live view* zavihek
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Medtem, ko je :ref:`*Schema definition* zavihek` namenjen definiciji v naprej definirane sheme oz. predloge objektov,
*Live view* zavihek omogoča direktno manipulacijo z objekti, ki so dodani delujoče ogrodje.

Na začetku zavihka se nahaja opcijski meni, v katerem je *add_object* funkcija, kateri lahko definiramo nov račun.
Ob kliku na gumb *Execute* bo definiran račun takoj dodan v DAF in začel z oglaševanjem.

Pod opcijskem menijem se nahajajo 3 gumbi. *Refresh* posodobi spodnji seznam z računi, ki oglašujejo v DAF, *Edit*
gumb odpre okno za definiranje računov, kjer se vanj naložijo obstoječe vrednosti iz uporabniškega računa, ki ga urejamo.
Okno poleg gumbov oz. pripomočkov, ki jih ima pri urejanju :ref:`Schema definition zavihku <*Schema definition* zavihek>`, vsebuje
tudi 2 dodatna gumba. Ta gumba sta *Refresh* gumb, ki v okno naloži osvežene vrednosti iz dejanskega objekta dodanega v DAF in 
*Live update* gumb, ki dejanski objekt v DAF, na novo inicializira z vrednostnimi definiranimi v oknu. Na dnu okna je znotraj
vijoličnega okvirja možno izvajanje metod (funkcij) na objektu.

.. figure:: ./DEP/images/gui-live-view-edit-account.png


*Output* zavihek
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Vse kar se nahaja v tem zavihku, je seznam izpisov, ki se izpišejo na standardnem izhodu stdout.
Uporabi se ga lahko za bolj podroben pregled kaj se dogaja z jedrom DAF.


.. figure:: ./DEP/images/gui-started-output-defined-accounts.png
    :width: 15cm

    Okno izpisov jedra ogrodja


*Analytics* zavihek
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Zavihek omogoča analizo poslanih sporočil in njihovo statistiko. Prav tako omogoča analizo pridruževanj preko sledenja
cehovskih povezav (angl. *Invite links*) in njihovo statistiko.

Za pridobitev vnosov, se uporabi gumb *Get logs*, ki na podlagi parametrov definiranih v zgornjem opcijskem meniju, vrne
v spodnji seznam filtrirane elemente. Te elemente se lahko vsakega posebej pregleda z gumbom *View log*, ki 
odpre okno za urejanje objektov.

Za pridobitev statistike se uporabi gumb *Calculate*, ki na podlagi opcijskega meniji nad gumbom, v spodnjo tabelo vrne podatke.


.. figure:: ./DEP/images/gui-analytics-message-frame-view-log.png
    :height: 10cm

    Prikaz vnosa o poslanem sporočilu.


.. figure:: ./DEP/images/gui-analytics-tab.png
    :width: 15cm

    Zavihek z analitiko / statistiko


.. raw:: latex

    \newpage



Povezava grafičnega vmesnika z jedrom ogrodja
---------------------------------------------------
Grafični vmesnik lahko s stališča lokacije delovanja deluje na dva načina. Prvi je lokalen način, kjer grafični vmesnik
z klikom na *Start* gumb zažene jedro ogrodja na istem računalniku, kot deluje grafični vmesnik. Drugi pa je oddaljen
način delovanja, kjer se grafični vmesnik poveže na HTTP strežnik, kateri deluje znotraj jedra ogrodja in na ta strežnik
pošilja HTTP ukaze, ki se v jedru mapirajo na programski vmesnik (API).

Za upravljanje z povezavo je bil ustvarjen ločen povezovalni nivo, ki sestoji iz dveh različnih objektov za povezovanje,
med katerimi lahko uporabnik izbira na vrhu grafičnega vmesnika.

.. figure:: ./DEP/images/gui-connection-select.png

    Izbira objekta za povezovanje

Za konfiguracijo oddaljenega dostopa je potrebno klikniti na gumb *Edit*, ki se nahaja na desni strani menija za izbiro
povezovalnega objekta. Prav tako je potrebno ustrezno konfigurirati jedro. Več o konfiguraciji je na voljo v
:ref:`dokumentaciji ogrodja <Remote control (GUI)>`.

.. figure:: ./DEP/daf-core-http-api.drawio.svg

    Povezava do jedra
