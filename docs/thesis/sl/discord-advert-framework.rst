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

.. |TextMESSAGE| replace:: :class:`~daf.message.TextMESSAGE`
.. |VoiceMESSAGE| replace:: :class:`~daf.message.VoiceMESSAGE`
.. |DirectMESSAGE| replace:: :class:`~daf.message.DirectMESSAGE`

.. note:: 

    Sledeča vsebina se včasih nanaša na objekte, ki niso opisani v diplomskem delu, so pa na voljo
    v uradni dokumentaciji projekta in sicer določeni objekti bodo ob kliku odprli uradno
    spletno dokumentacijo projekta |DAFDOC|_.



.. figure:: ./DEP/logo.png
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


Zasnova in razvoj (jedro)
============================
Jedro DAF-a je zasnovan kot Python_ knjižnica / paket, ki se jo lahko namesti preko PIP-a (*Preferred Installer Program*), ki je
vgrajen v Python_ in služi nalaganju Python paketov. Ker je DAF zasnovan kot ogrodje, ki lahko deluje neprekinjeno na strežniku,
ali pa kot GUI se ga lahko uporabi na dva načina in sicer kot:

1. Python paket, ki se ga vključi v ``.py`` Python_ skripto, v kateri se definira oglaševalsko shemo.
   
   .. literalinclude:: ./DEP/shill-script-example.py
      :language: python
      :caption: Primer definirane skripte

    
   Za več informacij glede definicije sheme glej |DAFDOC|_.


2. navaden program (deluje v Python_-u), ki se ga lahko zažene preko ukazne vrstice z ukazom ``daf-gui``, kar odpre
   grafični vmesnik.

   .. figure:: ./DEP/daf-gui-front.png
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


.. figure:: ./DEP/daf_abstraction.drawio.svg

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


.. figure:: ./DEP/daf-account-layer-flowchart.svg
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

.. figure:: ./DEP/daf-guild-layer-flowchart.svg
    :width: 500

    Delovanje cehovskega nivoja

|AutoGUILD| objekti omogočajo interno generacijo |GUILD| objektov na podlagi danega RegEx vzorca (``include_pattern``).
V primeru uporabe uporabniškega imena in gesla za prijavo na računskem nivoju, omogoča preko nivoja brskalnika
tudi avtomatično najdbo novih cehov in njihovo pridruževanje preko brskalnika (``auto_join`` parameter).
Osnovni del (generacija |GUILD| objektov) deluje tako da najprej preko nivoja abstrakcije Discord API najde, katerim
cehom je uporabnik pridružen in za vsak ceh, ki ustreza RegEx vzorcem ustvari nov |GUILD| objekt, ki ga interno hrani.
Vsak |GUILD| objekt podeduje parametre, ki jih je ob definiciji prejel |AutoGUILD|. Na koncu, ko so najde vse cehe,
vsakemu |GUILD| objektu da ukaz naj oglašuje, na enak način kot |GUILD| objektu da ta ukaz računski nivo.
Ta del bi lahko torej, s stališča abstrakcije, postavili nekje med računski nivo in cehovski nivo.

.. figure:: ./DEP/daf-guild-auto-layer-flowchart.svg
    :width: 600

    Delovanje AutoGUILD pod nivoja


.. raw:: latex

    \newpage


Sporočilni nivo
-----------------
Sporočilni nivo je zadolžen za pošiljanje dejanskih sporočil v posamezne kanale na Discord-u.
V tem nivoju so na voljo trije glavni razredi za ustvarjanje različnih vrst sporočil:

1. |TextMESSAGE| - pošiljanje tekstovnih sporočil v cehovske kanale
2. |VoiceMESSAGE| - predvajanje posnetkov v cehovskih kanalih
3. |DirectMESSAGE| - pošiljanje glasovnih sporočil v cehovske kanale.


|TextMESSAGE| in |DirectMESSAGE| sta si precej podobna, primarno gre v obeh primerih za tekstovna sporočila, razlika
je v kanalih ki jih |DirectMESSAGE| nima, temveč ta pošilja le sporočila v direktna sporočila uporabnika.
|VoiceMESSAGE| in |TextMESSAGE|, sta si po vrsti podatkov sicer različna, vendar pa oba pošiljata sporočila v kanale, ki
pripadata nekemu cehu in imata praktično enako inicializacijo.

Inicializacija |TextMESSAGE| in |VoiceMESSAGE| objektov poteka na sledeč način. Najprej preveri se podatkovni tip parametra
``channels``, ki predstavlja kanale kamor se bo sporočila pošiljalo in sicer obstajajo 2 možnosti podatkovnega tipa:

1. :class:`daf.message.AutoCHANNEL` - Je objekt, ki skrbi za avtomatično najdbo kanalov v cehu na podlagi nekega RegEx
   vzorca, podobno kot |AutoGUILD| v :ref:`cehovskem nivoju <Cehovski nivo>`.
   V tem primeru sporočilni nivo inicializira podani :class:`~daf.message.AutoCHANNEL` objekt.

2. :class:`list` (seznam), *snowflake* identifikatorjev (tipa :class:`int`) ali pa objektov iz ovojnega API nivoja, ki so lahko
   :class:`discord.TextChannel` za |TextMESSAGE| ali :class:`discord.VoiceChannel` za |VoiceMESSAGE| objekt.
   Inicializacija gre čez celoten seznam in v primeru *snowflake* identifikatorja za ta identifikator poskusi najti pripadajoči
   :class:`~discord.TextChannel` oz. :class:`~discord.VoiceChannel` objekt s tem identifikatorjem. Če pripadajočega
   objekta ne najde, se v terminalu izpiše opozorilo in inicializacija se nadaljuje na ostalih elementih v seznamu.
   V primeru neveljavnega tipa elementa v seznamu, inicializacija dvigne Python_ napako tipa :class:`TypeError`.
   V primeru da identifikator pripada kanalu, ki pripada nekem drugemu cehu, kot je ceh v katerem se nahaja trenutni 
   sporočilni objekt, inicializacija dvigne napako tipa :class:`ValueError`.

   V primeru |TextMESSAGE| objekta se na koncu še preveri če je podana perioda pošiljanja manjša od minimalnega
   čakanja počasnega načina (*Slow mode*) in periodo ustrezno popravi.


Inicializacija |DirectMESSAGE| objekta je precej bolj enostavna. Iz starša (|USER|) se pridobi objekt, ki na ovojnem API
nivoju predstavlja ceh in na tem objektu se kliče metoda :py:meth:`discord.User.create_dm`.
Metoda :py:meth:`~discord.User.create_dm` predstavlja analogijo na tekstovni kanal v cehu.


Medtem ko se inicializacija različnih vrst sporočilnih objektov razlikuje, je sama glavna logika večinoma enaka.
V cehovskem nivoju se od sporočilnega nivoja preko :py:meth:`~daf.message.TextMESSAGE._is_ready` metode preverja ali
je sporočilo pripravljeno za pošiljanje v slednjem primeru začne s procesom pošiljanja sporočila.

Kdaj je sporočilo pripravljeno za pošiljanje določa notranji atribut objekta, ki predstavlja točno specifičen čas naslednjega
pošiljanja sporočila. V primeru da je trenutni čas večji od tega atributa, je sporočilo pripravljeno za pošiljanje.
Ob ponastavitvi "časovnika" se ta atribut prišteje za konfigurirano periodo.
Torej dejanski čas pošiljanja ni relativen na prejšnji čas pošiljanja, temveč je relativen na predvideni čas pošiljanja.
Taka vrsta računanja časa omogoča določeno toleranco pri pošiljanju sporočila, saj se zaradi raznih zakasnitev in omejitev
zahtev na API v ovojnem API nivoju (pri pošiljanju vsakega sporočila in ostalih zahtev) dejansko sporočilo lahko pošlje kasneje kot predvideno.
To je še posebno pomembno v primeru da imamo definiranih veliko sporočil v enem računu, kar je zagotovilo da se sporočilo ne bo
poslalo točno ob določenem času. Ker se čas prišteva od prejšnjega časa pošiljanja, posledično to pomeni da bo v primeru
zamude sporočila, razmak med tem in naslednjim sporočilom manjši točno za to časovno napako (če privzamemo da ne bo ponovne zakasnitve).
Prvi čas pošiljanja je določen z ``start_in`` parametrom.
Primer časovne napake je prikazan na spodnji sliki.

.. figure:: ./DEP/daf-message-period.svg
    :width: 500

    Čas pošiljanja sporočila s toleranco zamud


.. raw:: latex

    \newpage


Proces pošiljanja sporočila poteka tako, da sporočilni nivo najprej pridobi podatke za pošiljanje. Ti podatki so lahko
fiksni podatki podani ob kreaciji sporočilnega objekta, lahko pa se jih pridobi tudi dinamično v primeru, da je bila
ob kreaciji objekta podana funkcija. V slednjem primeru se funkcijo pokliče in v primeru da vrne veljaven tip podatka za
vrsto sporočilnega objekta, se ta podatek uporabi pri pošiljanju sporočila - glej :func:`daf.dtypes.data_function`.
Po pridobivanju podatkov, sporočilni objekt za vsak svoj kanal preveri ali je uporabnik:

- še pridružen cehu,
- ima pravice za pošiljanje,
- kanal še obstaja.

Če karkoli od zgornjega ni res, se dvigne ustrezna Python_ napaka, ki simulira napako ovojnega API nivoja.
Tip dvignjene napake je podedovan iz :class:`discord.HTTPException`.
V primeru, da ni bila dvignjena nobena napaka, se sporočilo pošlje v kanal. Če je sporočilni objekt tipa
|TextMESSAGE| ali |DirectMESSAGE|, se lahko na podlagi ``mode`` parametra sporočilo pošlje na različne načine.

Po poslanem sporočilu se podatke sporočila in status pošiljanja pošlje :ref:`cehovskem novoju <Cehovski nivo>`.

.. figure:: ./DEP/daf-message-process.svg
    :width: 800

    Proces sporočilnega nivoja

.. raw:: latex

    \newpage

Nivo beleženja
---------------
Nivo beleženja je zadolžen za beleženje poslanih sporočil oz. beleženje poskusov pošiljanja sporočil. Podatke, ki jih
mora zabeležiti dobi neposredno iz :ref:`cehovskega nivoja <Cehovski nivo>`.

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


.. figure:: ./DEP/daf-high-level-log.svg
    :width: 500

    Višji nivo beleženja

.. raw:: latex

    \newpage

JSON beleženje
~~~~~~~~~~~~~~~~~
JSON beleženje je implementirano z objektom beleženja :class:`~daf.logging.LoggerJSON`.
Ta vrsta beleženja nima nobene specifične inicializacije, kliče se le inicializacijska metoda njegovega morebitnega
nadomestka.

Ob zahtevi beleženja objekt :class:`~daf.logging.LoggerJSON` najprej pogleda trenuten datum, iz katerega tvori
končno pot do datoteke od v parametrih podane osnovne poti. Končna pot je določena kot ``Leto/Mesec/Dan/<Ime Ceha>.json``.

To pot, v primeru da ne obstaja, ustvari in zatem z uporabo vgrajenega Python_ modula :mod:`json` podatke shrani v
datoteko. Za specifike glej :ref:`Logging (core)`.


.. figure:: ./DEP/daf-logging-json.svg
    :width: 300

    Process JSON beleženja

.. raw:: latex

    \newpage

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

.. figure:: ./DEP/sql_er.drawio.svg
    :width: 500

    SQL entitetno-relacijski diagram

Zgornja slika prikazuje povezavo posamezne tabele med seboj. Glavna tabela je :ref:`MessageLOG`.
Za opis posamezne tabele glej :ref:`SQL Tables`.

SQL inicializacija poteka v treh delih. Najprej se zgodi inicializacija :mod:`sqlalchemy`, kjer se vzpostavi povezava do
podatkovne baze. Podatkovna baza mora biti že vnaprej ustvarjena (razen SQLite), vendar ni potrebo ročno ustvarjati sheme (tabel).
Po vzpostavljeni povezavi, se ustvari celotna shema - tabele, objekti zaporedij (*Sequence*), in podobno.
Zatem se se v bazo v *lookup* tabele zapišejo določene konstantne vrednosti, kot so vrste sporočil, cehov za manjšo porabo podatkov
baze in na koncu se inicializira morebiten nadomestni objekt beleženja. Objekt beleženja za SQL je zdaj pripravljen za uporabo.

Ob zahtevi beleženja v bazo podatkoDa :class:`~daf.logging.LoggerJSON` najprej preveri ali je baza morda
v čakanju na ponovno povezavo (več opravil lahko čaka da se konča beleženje drugega opravila) in če čaka na povezavo, se
vrne v nivo beleženja, kjer beleženje opravi z nadomestnim objektom beleženja. V primeru povezane baze, objekt beleženja
iz začasne shrambe poskusi pridobiti od prej shranjene podatke (za pohitrenje beleženja) in če ti ne obstajajo, naredi
zahtevo po podatkih na podatkovno bazo. Nato se ustvari ORM objekt, ki predstavlja tabelo :ref:`MessageLOG` in znotraj
njega tudi ostali ORM objekti, ki predstavljajo tuje SQL ključe na druge relacije (tabele). Ustvarjeni ORM objekt
tabele :ref:`MessageLOG` se potem doda v bazo podatkov in v primeru da ni napak to pomeni konec beleženja. V primeru,
da se je zgodila kakršna koli napaka, se lahko SQL pod-nivo nivoja beleženja nanjo odzove na dva načina:

1. V primeru da je bila zaznana prekinitev povezave do baze, objekt SQL beleženja takoj nivoju beleženja da ukaz
   naj se beleženje permanentno izvaja na njegovem nadomestnem objektu in zatem se ustvari opravilo, ki čaka 5
   minut in se zatem poskusi povezati na podatkovno bazo. V primeru uspešne povezave na bazo se beleženje spet izvaja
   s SQL, v primeru neuspešne povezave pa čez 5 minut poskusi ponovno in nikoli ne neha poskušati.

2. V primeru da povezava ni prekinjena ampak je prišlo na primer do brisanja katere koli od tabel oz. *lookup* vrednosti,
   se shema ponovno poskusi postaviti. To poskuša narediti 5-krat in če se napaka ni odpravila, potem trenuten poskus
   pošiljanja zabeleži z nadomestim objektom beleženja, vendar le enkrat - naslednjič bo spet poizkusil z beleženjem SQL.


.. figure:: ./DEP/daf-logging-sql.svg
    :width: 500

    Proces beleženja z SQL podatkovno bazo


.. code-block:: python
    :caption: Izsek kode, ki prikazuje uporabo ORM za beleženje poslanega sporočila
    :linenos:

    # Save message log
    message_log_obj = MessageLOG(
        data_obj,
        message_type_obj,
        message_mode_obj,
        dm_success_info_reason,
        guild_obj,
        author_obj,
        [
            MessageChannelLOG(channel, reason)
            for channel, reason in _channels
        ],
    )
    session.add(message_log_obj)
    await self._run_async(session.commit)



Nivo brskalnika (Selenium)
-------------------------------
Velika večina DAF deluje na podlagi ovojnega API nivoja, kjer direktno komunicira z Discord API.
Določenih stvari se pa neposredno z API ne da narediti ali pa prek API
obstaja velika možnost, da Discord suspendira uporabnikov račun (npr. pridruževanje cehom), saj je po Discord ToS
uporaba avtomatiziranih računov prepovedana.

Za ta namen je bil ustvarjen nivo brskalnika, kjer DAF namesto komuniciranja z Discord API, komunicira z brskalnikom
Google Chrome. To opravlja s knjižnico `Selenium <https://www.selenium.dev/>`_, ki je namenjena avtomatizaciji brskalnikov
in se posledično uporablja tudi kot orodje za preizkušanje spletnih vmesnikov.

V DAF projektu, se ta knjižnica ne uporablja za testiranje, ampak za avtomatično prijavljanje v Discord z uporabniškim
imenom in geslom, ter tudi za pridruževanje cehom. Za to da bo ta nivo uporabljen, je potrebno ob ustvarjanju :class:`~daf.client.ACCOUNT`
objekta podati uporabniško ime in geslo namesto žetona. Znotraj :class:`~daf.client.ACCOUNT` objekta se bo potem samodejno
ustvaril nanj vezanj objekt :class:`~daf.web.SeleniumCLIENT`.

Prijavljanje v Discord z uporabniškim imenom in geslom poteka po sledečem načinu. Najprej se odpre brskalnik Chrome, na
katerega se poveže :class:`~daf.web.SeleniumCLIENT` in zatem :class:`~daf.web.SeleniumCLIENT` odpre URL 
https://discord.com/login. Ko se stran naloži, se vtipkata uporabniško ime in geslo, potem pa pa se klikne gumb "Login",
kar uporabnika prijavi v Discord. V primeru CAPTCHA (*Completely Automated Public Turing test to tell Computers and Humans Apart*)
okna, DAF čaka uporabnika da reši izziv. Po uspešni prijavi nivo brskalnika pošlje nivoju računa Discord prijavni žeton,
preko katerega se lahko ustvarja API klice. Nivo brskalnika hrani podatke prejšnje seje, tako da ob ponovnem zagonu ogrodja,
prijava ni ponovno potrebna.

Cehom se ogrodje pridružuje po sledečem postopku. Najprej naključno klika po seznamu strežnikov, da poskusi simulirati
človeško obnašanje in zmanjša možnost za pojav CAPTCHA testa. Zatem klikne na *Join server* gumb, ki pokaže okno za vpis
cehovske povezave, kjer to povezavo vpiše in klikne na gumb *Join*. Na koncu potrdi še morebitna pravila, preko Discord sistema
pravil. Velika možnost je da bo moral uporabnik opraviti potrdilo še na drug način, ki ni definiran prek Discord platforme -
npr. preko robotskega računa (*Bot*), ki ga ima ceh. Cehe, ki se jim bo pridružil najde preko https://top.gg platforme oz.
preko :class:`daf.web.GuildDISCOVERY` in sicer je ta del definiran v :ref:`cehovskem nivoju <Cehovski nivo>`.


Ovojni Discord API nivo
-----------------------------
Nivo, ki ovija Discord API ni striktno del samega ogrodja, ampak je to knjižnica oz. ogrodje `Pycord <https://docs.pycord.dev/en/stable/>`_.
PyCord je odprto-kodno ogrodje, ki je nastalo iz kode starejšega `discord.py <https://discordpy.readthedocs.io/en/stable/>`_.
Razlog da ga tu imenujem ogrodje, je da poleg tega da ponuja abstrakcijo Discord API, PyCord interno za vsak račun ustvari
tudi svoje :mod:`asyncio` opravilo, ki na podlagi dogodkov iz Discord "Gateway"-a (uradno ime) posodablja svoje objekte,
kot so :class:`~discord.TextChannel`, :class:`~discord.Guild`, :class:`~discord.User` in druge. Na primer, če bi imeli nekje
shranjen objekt :class:`discord.Guild` in bi pripadajočem cehu spremenili ime, bi se ta sprememba takoj poznala v 
:class:`~discord.Guild` objektu. Vsi objekti v Python_-u  se kopirajo po referenci, zato se spremembe poznajo na vseh kopijah.
Ogrodje PyCord skoraj popolnoma zakrije Discord API z raznimi objekti, ki jih DAF interno uporablja.

Če bi si ogledali izvirno kodo DAF, bi opazili da je poleg ``daf`` paketa zraven tudi paket z imenom ``_discord``.
To ni nič drugega, kot PyCord ogrodje, le da je modificirano za možnost rabe na osebnih uporabniških računih.
Za možno posodabljanje PyCord ogrodja, so ustvarjene GIT datoteke za krpanje (*patch*) - ustvarjene z ukazom ``git diff``,
kar daje možnost enostavne menjave za novejšo verzijo PyCord ogrodja,
na kateri se potem z ukazom ``git apply`` spremembe prenese na posodobljeno verzijo.

Več o tem nivoju se lahko izve na https://docs.pycord.dev/en/stable/.



Zasnova in razvoj (grafični vmesnik [GUI])
============================================
DAF lahko deluje popolnoma brez grafičnega vmesnika, a ta način zahteva pisanje *.py* datotek oz. Python skript, kar
ja marskikomu težje, sploh če se še nikoli niso srečali s Python jezikom.

V namen enostavnejše izkušnje pri uporabi ogrodja, obstaja grafični vmesnik, ki deluje ločeno od samega ogrodja, z njim pa
komunicira preko njegovih kontrolnih funkcij, ki se nahajajo v :ref:`jedrnem nivoju <Jedrni nivo>`.

.. figure:: ./DEP/daf-gui-front.png
    :width: 15cm

    Grafični vmesnik (privzet prikaz)

.. raw:: latex

    \newpage

Kot je razvidno iz gornje slike, je za dizajn vmesnika izbran svetel dizajn z modrimi odtenki za posamezne elemente.


Tkinter
------------------
Za izdelavo grafičnega vmesnika je bila uporabljena knjižnica `ttkboostrap <https://ttkbootstrap.readthedocs.io/en/latest/>`_, ki je razširitev
vgrajene Python_ knjižnice :mod:`tkinter`.

Tkinter knjižnica je v osnovi vmesnik na Tcl/Tk orodja za izdelavo grafičnih vmesnikov, doda pa tudi nekaj svojih nivojev,
ki še dodatno razširijo delovanje knjižnice.

Tkinter omogoča definicijo različnih pripomočkov (angl. *widgets*), ki se jih da dodatno razširiti in shraniti pod nove
pripomočke, katere lahko večkrat uporabimo. Ti pripomočki so naprimer :class:`ttk.Combobox`, ki je neke vrste 
(angl.) "drop-down" meni, :class:`ttk.Spinbox` za vnašanje številkških vrednosti, gumbi :class:`ttk.Button`, itd.
Posamezne pripomočke se da tudi znatno konfigurirati, kjer lahko spreminjamo stile, velikost, pisavo, ipd.

Več o Tkinter knjižnici si lahko preberete na uradni Python dokumentaciji :mod:`tukaj <tkinter>`.


Zavihki
----------------------
Grafični vmesnik DAF je razdeljen na več zavihkov, kjer je vsak namenjen svoji stvari.


*Optional modules* zavihek
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Ta zavihek omogoča namestitev dodatnih funkcionalnosti, ki v osnovem DAF paketu niso prisotni (za hitrejši zagon in namestitveni čas).
Sestavljen je iz statusnih panelov, ki če so rdeči (modul ni nameščen) vsebuje še gumb za namestitev.
Gumb bo namestil potrebne pakete, potem pa bo vmesnik uporabniku sporočil, da mora za spremembe ponovno odpreti vmesnik.
Ob ponovnem odprtju po namestitvi bo statusni panel za posamezen modul obarvan zelen.

*Schema definition* zavihek
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Zavihek omogoča definicijo uporabniških računov (in v njih cehov, sporočil, ...), definicijo upravljalnika za beleženje.
Omogoča tudi shrambo teh definicij v JSON datoteko, braje definicij iz JSON datoteke in pa generacijo ekvivalentne
*.py* datoteke, ki deluje v samem jedru DAF (brez grafičnega vmesnika - :ref:`Zasnova in razvoj (jedro)`).

.. figure:: ./DEP/images/gui-schema-restore-bnt.png
    :width: 15cm

    Zavihek za definicijo sheme

Omogoča tudi dinamično branje in pretvorbo objektov v že zagnanem vmesniku preko gumbov, ki vsebujejo besedo *live*.

Uporabniške račune se lahko definira tako, da ob kliku na opcijski meni *Object options*, uporabniki izberejo opcijo *New ACCOUNT*.
Ob kliku se nam odpre novo okno, ki je avtomatično in dinamično generirano iz podatkov o podatkovnih tipih (anotacije), ki jih sprejme
razred ob definiciji. V oknu se za vsak parameter generira labela, opcijski meni in pa opcijski gumb, v katerem lahko urejamo izbrano vrednost
oz. definiramo novo vrednost.

.. figure:: ./DEP/images/gui-new-item-define.png

    Definicija uporabiškega računa

.. raw:: latex

    \newpage

Na zgornji sliki je mogoče opaziti tudi 3 gumbe, ki so prisotni v definicijskem oknu vedno, ne glede na to katere objekte definiramo.
Ti so *Save*, *Close* in *Keep on top*. *Save* gumb bo shranil vrednosti okna v abstrakten objekt ObjectInfo in ga shranil v prejšen GUI pripomoček (*Listbox* ali Opcijski meni).
*Close* gumb bo poskušal zapreti okno in če je bila v oknu narejena sprememba, okno vpraša uporabnika, če želi shraniti trenutne vrednosti.
*Keep on top* gumb pa prisili, da bo okno vedno prikazano na vrhu ostalih oken v operacijskem sistemu.
Opazimo pa tudi gumb *Help*. Ta gumb ni vedno prisoten, ampak je na voljo le če urejamo objekte, ki so del DAF ogrodja, PyCord ogrodja ali pa del
vgrajene Python_ knjižnice. Klik na ta gumb bo v brskalniku odprl dokumentacijo pripadajočega modula objekta in v iskalnik dokumentacije vpisal ime objekta.
Na tak način lahko uporabniki zelo hitro najdejo objekt v dokumentaciji brez dolgočasnega branja le te.


.. figure:: ./DEP/images/gui-help-search.png
    :width: 15cm

    Primer odprte dokumentacije ob kliku na gumb *Help* znotraj okna za definicijo
    :class:`~daf.client.ACCOUNT` objekta.


.. note::

    Za nekatere objekte, bodo prikazani tudi dodatni gumbi. Te gumbi so npr. gumb, ki odpre pripomoček za izbiro barve (:class:`discord.Colour`),
    pripomoček za izbiro datoteke oz. mape (:class:`~daf.dtypes.FILE`, :class:`~daf.dtypes.AUDIO`, :class:`~daf.logging.LoggerJSON`, :class:`~daf.logging.LoggerCSV`) ipd.


Upravljalnik za beleženje definiramo tako, da v desnem okvirju zavihka v meniju izberemo vrsto upravljalnika 
za logiranje in za spremembo parametrov kliknemo na gumb *Edit*. Odpre se definicijsko okno, ki deluje na enak način kot za definicijo
uporabniških računov.


.. figure:: ./DEP/images/gui-logger-definition-edit-json.png
    :width: 15cm

    Definicija upravljalnika beleženja


Pod izbiro za upravljalnik se nahaja tudi opcijski meni za izbiro nivoja izpisov v *Output* zavihku.


*Live view* zavihek
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Medtem, ko je :ref:`*Schema definition* zavihek` namenjen definiciji v naprej definirane sheme oz. predloge objektov,
*Live view* zavihek omogoča direktno manipulacijo z objekti, ki so dejansko dodani in delujejo v DAF in predstavljajo prave objekte.

Na začetku zavihka se nahaja opcijski meni, v katerem je *add_object* funkcija, kateri lahko definiramo nov račun.
Ob kliku na gumb *Execute* bo definiran račun takoj dodan v DAF in začel z oglaševanjem.

Pod opcijskem menijem se nahajajo 3 gumbi. *Refresh* posodobi spodnji seznam z računi, ki oglašujejo v DAF, *Edit*
gumb odpre okno za definiranje računov, kjer se vanj naložijo obstoječe vrednosti iz uporabniškega računa, ki ga urejamo.
Okno poleg gumbov oz. pripomočkov, ki jih ima pri urejanju :ref:`Schema definition zavihku <*Schema definition* zavihek>`, vsebuje
tudi 2 dodatna gumba. Ta gumba sta *Refresh* gumb, ki v okno naloži osvežene vrednosti iz dejanskega objekta dodanega v DAF in 
*Live update* gumb, ki dejanski objekt v DAF, na novo inicializira z vrednostnimi definiranimi v oknu.


*Output* zavihek
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Vse kar se nahaja v tem zavihku, je seznam izpisov, ki se izpišejo na standardnem izhodu stdout.
Uporabi se ga lahko za bolj podroben pregled kaj se dogaja z jedrom DAF.


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
