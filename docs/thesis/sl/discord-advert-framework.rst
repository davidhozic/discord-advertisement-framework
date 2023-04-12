==================================================
Projekt (DAF)
==================================================

DAF - *Discord Advertisement Framework*

.. _Python: https://www.python.org

.. _DAFDOC: https://daf.davidhozic.com

.. |DAFDOC| replace:: DAF dokumentacija

.. |USER| replace:: :class:`~daf.guild.USER`
.. |GUILD| replace:: :class:`~daf.guild.GUILD`
.. |AutoGUILD| replace:: :class:`~daf.guild.AutoGUILD`

.. note:: 

    Sledeča vsebina se včasih nanaša na objekte, ki niso opisani v diplomskem delu, so pa na voljo
    v uradni dokumentaciji projekta in sicer določeni objekti bodo ob kliku odprli uradno
    spletno dokumentacijo projekta |DAFDOC|_.



.. figure:: ./DEP/images/logo.png
    :width: 3cm

    Discord Advertisement Framework logo

    (Narejeno z DALL-E & Adobe Photoshop)


Namen projekta
=================
Pobudo za projekt sem prejel od kolega,
ki je za svoj projekt povezan z nezamenljivimi žetoni potreboval orodje, ki bi po več dni v tednu lahko
neprestano samodejno oglaševal njegov projekt po različnih cehih.

Cilj projekta je izdelati ogrodje, ki lahko deluje 24 ur na dan in samodejno oglašuje v naprej definirano vsebino ali
pa tudi dinamično vsebino, omogoča pregled poslanih sporočil in poročanje o uspešnosti preko beleženja zgodovine
poslanih sporočil.
Ker naj bi to ogrodje delovalo brez prekinitev je cilj ogrodje narediti, da bo delovalo kot demonski proces v ozadju
brez grafičnega vmesnika. Vendar je pa definicija brez grafičnega vmesnika težja in zahteva malo več dela, zato je cilj izdelati
tudi grafični vmesnik, ki bo deloval kot dodaten nivo nad samim ogrodjem in bo omogočal generacijo oglaševalske skripte, 
ki se jo lahko potem zažene na strežniku brez grafičnega vmesnika za neprekinjeno oglaševanje. Za lažji pregled dogajanja
na strežniku, je cilj na grafičnem vmesniku implementirati možnost oddaljenega dostopa, ki bo omogočal direktno manipulacijo
oglaševalske sheme in pregled zgodovine poslanih sporočil za določitev uspešnosti oglaševanja.


.. figure:: ./DEP/images/daf_goal_design.svg
    :width: 800

    Skica osnovne ideje


Zasnova in razvoj
==================
DAF je zasnovan kot Python_ knjižnica / paket, ki se jo lahko namesti preko PIP-a (*Preferred Installer Program*), ki je
vgrajen v Python_ in služi nalaganju Python paketov. Ker je DAF zasnovan kot ogrodje, ki lahko deluje neprekinjeno na strežniku,
ali pa kot GUI se ga lahko uporabi na dva načina in sicer kot:

1. Python paket, ki se ga vključi v ``.py`` Python_ skripto, v kateri se definira oglaševalsko shemo.
   
   .. literalinclude:: ./DEP/images/shill-script-example.py
      :language: python
      :caption: Primer definirane skripte

    
   Za več informacij glede definicije sheme glej |DAFDOC|_.


2. navaden program (deluje v Python_-u), ki se ga lahko zažene preko ukazne vrstice z ukazom ``daf-gui``, kar odpre
   grafični vmesnik.

   .. figure:: ./DEP/images/daf-gui-front.png
      :width: 12cm

      Grafični vmesnik

.. raw:: latex

    \newpage

V obeh zgornjih primerih celotno ogrodje deluje znotraj opravil, ki se jih ustvari z  modulom :mod:`asyncio`, ki je eden 
iz med več vgrajenih Python_ modulov.


Za lažjo implementacijo in kasnejši razvoj, je DAF razdeljen na več nivojev abstrakcije oziroma plasti.
Ti nivoji so:

- Jedrni nivo
- Uporabniški nivo
- Cehovski (strežniški) nivo
- Sporočilni nivo
- Nivo beleženja zgodovine
- Nivo brskalnika (Selenium)
- Ovojni nivo Discord API


.. figure:: ./DEP/images/daf_abstraction.drawio.svg

    Abstrakcija


Kot dodaten nivo bi lahko šteli še grafični vmesnik a je ta ločen od glavnega paketa, za to zgoraj ni pisan.


Jedrni nivo
-------------
Jedrni nivo skrbi za zagon samega ogrodja ter njegovo zaustavitev. Skrbi tudi za procesiranje ukazov, ki jih DAF ponuja
preko lastnega vmesnika in tudi dodajanje in odstranjevanje objektov.

Ko zaženemo ogrodje, ta v jedrnem nivoju sproži inicializacijo nivoja beleženja in zatem uporabniškega nivoja,
kjer za vsak definiran uporabniški račun, ustvari lastno :mod:`asyncio` opravilo, ki omogoča simultano oglaševanje po več računih hkrati.
Na koncu pokliče funkcijo, ki je bila dana ob klicu zaganjalne funkcije :func:`daf.core.run`.

Ta nivo sam po sebi nima nobenih opravil, ki bi neprestano karkoli opravljala, razen enega opravila, ki skrbi
za čiščenje uporabniških računov v primeru, da so se ti zaradi neke napake sami zaprli. V primeru da napake ni,
se račune dodaja preko :func:`daf.core.add_object` in briše preko :func:`daf.core.remove_object` funkcij.



Računski nivo
---------------

Računski nivo je zadolžen za upravljanjem z uporabniškimi računi. Vse kar se dogaja v tem nivoju se zgodi preko
:class:`daf.client.ACCOUNT` objekta.

Računski nivo skrbi za inicializacijo nivoja, ki ovija Discord API in za upravljanje opravila, ki komunicira z
cehovskim nivojem.

Ob dodajanju novega računa v ogrodje, jedrni nivo za vsak definiran račun pokliče :py:meth:`daf.client.ACCOUNT.initialize` metodo, ki
v primeru da sta bila podana uporabniško ime in geslo, da ukaz nivoju brskalnika naj se prijavi preko uradne Discord
aplikacije in potem uporabniški žeton pošlje nazaj uporabniškemu nivoju. Ko ima uporabniški nivo žeton
(preko direktne podaje s parametrom ali preko nivoja brskalnika), da ovojnem API nivoju ukaz naj se ustvari nova
povezava in klient za dostop do Discord'a (:class:`discord.Client`)  s podanim računom, kjer se ta klient veže na trenuten :class:`~daf.client.ACCOUNT`
objekt. Prav tako se na trenuten :class:`~daf.client.ACCOUNT` objekt veže morebiten klient nivoja brskalnika (:class:`daf.web.SeleniumCLIENT`).
Na koncu se za posamezen definiran ceh, da cehovskem nivoju še ukaz za inicializacijo le tega in ustvari še glavno
opravilo vezano na specifičen uporabniški račun.


.. figure:: ./DEP/images/daf-account-layer-flowchart.svg
    :width: 500

    Delovanje računskega nivoja


.. raw:: latex

    \newpage


Cehovski nivo
---------------
Cehovski nivo je primarno zadolžen za upravljanje s cehi in komuniciranje s sporočilnim nivojem. V primeru
naprednejših funkcionalnostih, kot je avtomatično pridruževanje cehom, komunicira tudi z nivojem brskalnika.

Nivoju pripadajo trije razredi:

- |GUILD|
- |USER|
- |AutoGUILD|

|GUILD| in |USER| sta med seboj praktično enaka, edina razlika med njima je ta,
da |USER| predstavlja osebe katerim bomo pošiljali sporočila, |GUILD| pa predstavlja
cehe z kanali.

|AutoGUILD| pa po drugi strani sam po sebi ne predstavlja točno specifičnega ceha, ampak več cehov, katerih ime
se ujema z podanim RegEx vzorcem.

Inicializacija |GUILD| in |USER| je preprosta. Na podlagi parametra ``snowflake``, ki predstavlja Discord-ov
unikaten identifikator, pridobi objekt, ki predstavlja nek ceh oz. uporabnika v nivoju abstrakcije Discord API in za
vsak objekt, ki predstavlja sporočilo, pošlje sporočilnem nivoju ukaz naj se sporočilo inicializira.

|GUILD| in |USER| na začetku glavne metode najprej vprašata sporočilni nivo za sporočila, ki jih je potrebno odstraniti
(``remove_after`` parameter sporočila), in ta sporočila odstranita iz svoje shrambe. Zatem povprašata po sporočilih, ki
so pripravljeni za pošiljanje (jim je potekla perioda) ter sporočilnemu nivoju, za posamezno sporočilo, pošlje ukaz naj se
sporočilo pošlje. Od sporočilnega nivoja prejme informacije o poslanem sporočilu oz. neuspelem poskusu pošiljanja, kar
cehovski nivo pošlje nivoju beleženja. Poleg informacij o sporočilu, prejme cehovski nivo od sporočilnega nivoja
tudi morebitno informacijo da je bil ceh zbrisan, oz. je bil uporabnik odstranjen iz ceha kar posledično pomeni da je
potrebno |GUILD| / |USER| objekt zbrisati preko računskega nivoja.

.. figure:: ./DEP/images/daf-guild-layer-flowchart.svg
    :width: 500

    Delovanje cehovskega nivoja

|AutoGUILD| objekti omogočajo interno generacijo |GUILD| objektov na podlagi danega RegEx vzorca (``include_pattern``).
V primeru uporabe uporabniškega imena in gesla za prijavo na računskem nivoju, omogoča preko nivoja brskalnika
tudi avtomatično najdbo novih cehov in njihovo pridruževanje preko brskalnika.
Osnovni del (generacija |GUILD| objektov) deluje tako da najprej preko nivoja abstrakcije Discord API najde, katerim
cehom je uporabnik pridružen in za vsak ceh, ki ustreza RegEx vzorcem ustvari nov |GUILD| objekt, ki ga interno hrani.
Vsak |GUILD| objekt podeduje parametre, ki jih je ob definiciji prejel |AutoGUILD|. Na koncu, ko so najde vse cehe,
vsakemu |GUILD| objektu da ukaz naj oglašuje, na enak način kot |GUILD| objektu da ta ukaz računski nivo.
Ta del bi lahko torej, s stališča abstrakcije, postavili nekje med računski nivo in cehovski nivo.

.. figure:: ./DEP/images/daf-guild-auto-layer-flowchart.svg
    :width: 500

    Delovanje AutoGUILD pod nivoja


.. raw:: latex

    \newpage


Sporočilni nivo
-----------------
.. error:: TODO: Write

Nivo beleženja
---------------
Nivo beleženja je zadolžen za beleženje poslanih sporočil oz. beleženje poskusov pošiljanja sporočil. Podatke, ki jih
mora zabeležiti dobi neposredno iz cehovskega nivoja (:ref:`Cehovski nivo`).

DAF omogoča beleženje v tri različne formate, kjer vsakemu pripada lasten objekt beleženja:

1. JSON - :class:`~daf.logging.LoggerJSON`
2. CSV (nekatera polja so JSON) - :class:`~daf.logging.LoggerCSV`
3. SQL (*Structured Query Language*) - :class:`~daf.logging.sql.LoggerSQL`


Ob inicializaciji, se v jedrnem nivoju poda željen objekt beleženja, ki se inicializira in shrani v nivo beleženja.
V postopku inicializaciji po svoji lastni inicializaciji, inicializira še njegov nadomestni (``fallback`` parameter)
objekt, ki se uporabi v primeru kakršne koli napake pri beleženju (bolj pomembno pri SQL beleženju na oddaljen strežnik).

Po vsakem poslanem sporočilu se iz cehovskega nivoja naredi zahteva, ki vsebuje podatke o cehu, poslanem sporočilu oz.
poskusu pošiljanja ter podatki o uporabniškem računu, ki je sporočilo poslal. Nivo beleženja posreduje zahtevo
izbranem objektu beleženja, ki v primeru napake dvigne Python_ napako (*exception*), na kar nivo beleženja 
reagira tako, da začasno zamenja objekt beleženja na njegov nadomestek in spet poskusi. Poskuša dokler mu ne
zmanjka nadomestkov ali pa je beleženje uspešno.


.. figure:: ./DEP/images/daf-high-level-log.svg
    :width: 500

    Višji nivo beleženja

JSON beleženje
~~~~~~~~~~~~~~~~~
JSON beleženje je implementirano z objektom beleženja :class:`~daf.logging.LoggerJSON`.
Ta vrsta beleženja nima nobene specifične inicializacije, kliče se le inicializacijska metoda njegovega morebitnega
nadomestka.

Ob zahtevi beleženja objekt :class:`~daf.logging.LoggerJSON` najprej pogleda trenuten datum, iz katerega tvori
končno pot do datoteke od v parametrih podane osnovne poti. Končna pot je določena kot ``Leto/Mesec/Dan/<Ime Ceha>.json``.

To pot, v primeru da ne obstaja, ustvari in zatem z uporabo vgrajenega Python_ modula :mod:`json` podatke shrani v
datoteko. Za specifike glej :ref:`Logging (core)`.


.. figure:: ./DEP/images/daf-logging-json.svg
    :width: 300

    Process JSON beleženja


CSV beleženje
~~~~~~~~~~~~~~~~~~
CSV beleženje deluje na enak način kot :ref:`JSON beleženje`. Edina razlika je v formatu, kjer je format tu CSV.
Lokacija datotek je enaka kot pri :ref:`JSON beleženje`. Za shranjevanje je uporabljen vgrajen Python_ modul :mod:`csv`.


SQL beleženje
~~~~~~~~~~~~~~~~~~
SQL beleženja pa deluje precej drugače kot :ref:`JSON beleženje` in :ref:`CSV beleženje`. Medtem ko sicer omogoča tudi shranjevanje
v datoteke, so te datoteke dejansko baze podatkov SQLite.

DAF omogoča beleženje v 4 dialekte:

1. SQLite
2. Microsoft SQL Server (mssql)
3. PostgreSQL
4. MySQL / MariaDB

Za čim bolj univerzalno implementacijo na vseh dialektih, je bila pri razvoju uporabljena knjižnica :mod:`SQLAlchemy`.
Celoten sistem SQL beleženja je implementiran s pomočjo ORM (*Object relational mapping*), kar med drugim omogoča tudi
da SQL tabele predstavimo z Python_ razredi, posamezne vnose v bazo podatkov oz. vrstice pa predstavimo z instancami
teh razredov. Z ORM lahko skoraj v celoti skrijemo SQL in delamo neposredno z Python_ objekti, ki so lahko tudi gnezdene
strukture, npr. vnosa dveh ločenih tabel lahko predstavimo z dvema ločenima instancama, kjer je ena instanca znotraj
druge instance.

.. figure:: ./DEP/images/sql_er.drawio.svg

    SQL entitetno-relacijski diagram

Zgornja slika prikazuje povezavo posamezne tabele med seboj. Glavna tabela je :ref:`MessageLOG`.
Za opis posamezne tabele glej :ref:`Logging (core)`.

SQL inicializacija poteka v treh delih. Najprej se zgodi inicializacija :mod:`sqlalchemy`, kjer se vzpostavi povezava do
podatkovne baze. Podatkovna baza mora biti že vnaprej ustvarjena (razen SQLite), vendar ni potrebo ročno ustvarjati sheme (tabel).
Po vzpostavljeni povezavi, se ustvari celotna shema - tabele, objekti zaporedij (*Sequence*), in podobno.
Zatem se se v bazo v *lookup* tabele zapišejo določene konstantne vrednosti, kot so vrste sporočil, cehov za manjšo porabo podatkov
baze in na koncu se inicializira morebiten nadomestni objekt beleženja. Objekt beleženja za SQL je zdaj pripravljen za uporabo.

Proces beleženja v bazo je malo bolj kompleksen, zato tu ni na dolgo napisan in je spodaj diagram, ki prikazuje
celoten process.

Je morda smiselno poudariti procesiranje napak v bazi. V primeru da se v procesu beleženja zgodi kakršna koli napaka, se bo
proces odzval na dva možna načina:

1. V primeru da je bila zaznana prekinitev povezave do baze, objekt SQL beleženja takoj nivoju beleženja da ukaz
   naj se beleženje permanentno izvaja na njegovem nadomestnem objektu in zatem se ustvari opravilo, ki čaka 5
   minut in se zatem poskusi povezati na podatkovno bazo. V primeru uspešne povezave na bazo se beleženje spet izvaja
   s SQL, v primeru neuspešne povezave pa čez 5 minut poskusi ponovno in nikoli ne neha poskušati.

2. V primeru da povezava ni prekinjena ampak je prišlo na primer do brisanja katere koli od tabel oz. *lookup* vrednosti,
   se shema ponovno poskusi postaviti. To poskuša narediti 5-krat in če se napaka ni odpravila, potem trenuten poskus
   pošiljanja zabeleži z nadomestim objektom beleženja, vendar le enkrat - naslednjič bo spet poizkusil z beleženjem SQL.



.. figure:: ./DEP/images/sql_logging_process.drawio.svg

    Proces beleženja z SQL podatkovno bazo

