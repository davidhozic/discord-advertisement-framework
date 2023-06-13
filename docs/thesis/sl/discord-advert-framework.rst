==================================================
Ogrodje za oglaševanje v Discord
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

    Sledeča vsebina se včasih nanaša na objekte, ki niso podrobno
    opisani v diplomskem delu, so pa na voljo v uradni dokumentaciji projekta
    in sicer določeni objekti bodo ob kliku odprli uradno spletno dokumentacijo projekta |DAFDOC|_.



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


Zasnova in razvoj jedra
============================
Jedro DAF-a je zasnovan kot Python_ knjižnica / paket, ki se jo lahko namesti preko PIP-a (*Preferred Installer Program*), ki je
vgrajen v Python_ in služi nalaganju Python paketov. Za uporabo jedra mora uporabniki ustvariti ``.py`` datoteko in definirati
ustrezno konfiguracijo. To zahteva nekaj osnovnega znanja Python jezika, obstaja pa tudi možnost, da se to datoteko
generira iz grafičnega vmesnika (:ref:`Zasnova in razvoj grafičnega vmesnika`)

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


Jedrni nivo
-------------
Jedrni nivo skrbi za zagon samega ogrodja ter njegovo zaustavitev. Skrbi tudi za procesiranje ukazov, ki jih DAF ponuja
preko lastnega vmesnika in tudi dodajanje in odstranjevanje objektov.

Ko zaženemo ogrodje, ta v jedrnem nivoju sproži inicializacijo nivoja beleženja in zatem uporabniškega nivoja,
kjer za vsak definiran uporabniški račun, ustvari lastno :mod:`asyncio` opravilo, ki omogoča simultano oglaševanje po več računih hkrati.
Na koncu pokliče funkcijo, ki je bila dana ob klicu zaganjalne funkcije :func:`daf.core.run`.

Jedrni nivo ima vedno vsaj eno opravilo, in sicer je to tisto, ki skrbi za čiščenje uporabniških računov, v primeru napak.
V primeru da napake ni, se račune dodaja preko :func:`daf.core.add_object` in
briše preko :func:`daf.core.remove_object` funkcij

Drugo opravilo se zažene le v primeru, da je vklopljeno shranjevanje objektov v datoteko (preko :func:`~daf.core.run` funkcije).
Ogrodje samo po sebi deluje, tako da ima vse objekte (računov, cehov, sporočil, ipd.) shranjene kar neposredno v RAM pomnilniku.
Že od samega začetka je ogrodje narejeno na tak način da se željene objekte definira kar preko Python skripte in je zato shranjevanje v RAM
ob taki definiciji neproblematično, problem pa je nastopil, ko je bilo dodano dinamično dodajanje in brisanje objektov, kar
dejansko uporabnikom omogoča da ogrodje dinamično uporavljajo in v tem primeru je bilo potrebno dodati neke vrste permanetno shrambo.
Razmišljalo se je o več alternativah, ena izmed njih je bila da bi se vse objekte shranjevalo v neko bazo podatkov, ki bi omogočala
mapiranje podatkov v bazi na Python objekte, kar bi z vidika robustnosti bila zelo dobra izbira, a to bi zahtevalo ogromno prenovo
vseh nivojev, zato se je na koncu izbrala preprosta opcija shranjevanja objektov, ki preko :mod:`pickle` modula shrani vse račune
ob vsakem normalnem izklopu ogrodja ali pa v vsakem primeru na dve minuti v primeru neprimerne ustavitve. V prihodnosti, so
še vedno načrti za izboljšanje tega mehanizma in se ne izključuje opcija uporabe prej omenjene podatkovne baze.


Računski nivo
---------------

Računski nivo je zadolžen za upravljanjem z uporabniškimi računi. Vse kar se dogaja v tem nivoju se zgodi preko
:class:`daf.client.ACCOUNT` objekta.

Računski nivo skrbi za inicializacijo nivoja, ki ovija Discord API in za upravljanje opravila, ki komunicira z
cehovskim nivojem.


Možnost rabe večih uporabniških računov je na voljo od verzije 2.4 naprej, pred tem pa je bila možnost rabe le enega računa,
je bilo pa mogoče več računov definirati preprosto tako da se je ustvarilo več skript z različnimi uporabniškimi žetoni (alternativa geslu),
in zagnalo nov proces v operacijskem sistemu. Zagon v večih procesih je bil morda z performančnega vidika bolje,
saj je bilo posledično za delovanje uporabljenih tudi več procesorskih jedr. Glede da ogrodjo za svoje delovanje dejansko
ne potrebuje skoraj nobene moči in bi ga lahko zaganjali tudi na vgrajenih napravah, pa dejansko to ni noben problem.

.. Ob dodajanju novega računa v ogrodje, jedrni nivo za vsak definiran račun pokliče :py:meth:`daf.client.ACCOUNT.initialize` metodo, ki
.. v primeru da sta bila podana uporabniško ime in geslo, da ukaz nivoju brskalnika naj se prijavi preko uradne Discord
.. aplikacije in potem uporabniški žeton pošlje nazaj uporabniškemu nivoju. Ko ima uporabniški nivo žeton
.. (preko direktne podaje s parametrom ali preko nivoja brskalnika), da ovojnem API nivoju ukaz naj se ustvari nova
.. povezava in klient za dostop do Discord'a (:class:`discord.Client`)  s podanim računom, kjer se ta klient veže na trenuten :class:`~daf.client.ACCOUNT`
.. objekt. Prav tako se na trenuten :class:`~daf.client.ACCOUNT` objekt veže morebiten klient nivoja brskalnika (:class:`daf.web.SeleniumCLIENT`).
.. Na koncu se za posamezen definiran ceh, da cehovskem nivoju še ukaz za inicializacijo le tega in ustvari še glavno
.. opravilo vezano na specifičen uporabniški račun.


.. figure:: ./DEP/daf-account-layer-flowchart.svg
    :width: 500

    Delovanje računskega nivoja



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

Sam cehovski nivo na začetku razvoja sploh ni bil potreben, a je bil vseeno dodan preprosto zaradi boljše preglednosti,
ne samo notranje kode, ampak tudi kode za definiranje same oglaševalske datoteke ob velikem številu sporočil.
To je sicer posledično zahtevalo definicijo dodatnih vrstic, kar je hitro postalo opazno ob 90tih različnih cehih.
Vseeno se je ta izbira dobro izšla, saj je zdaj na cehovskem nivoju veliko funkcionalnosti, ki ne spada v ostale nivoje, 
kot je na primer avtomatično iskanje novih cehov, in njihovo pridruževanje. Ta abstrakcija nudi tudi veliko preglednosti
v primeru logiranja (vsaj V JSON datoteke), kjer je vse razdeljeno po različnih cehih.


.. figure:: ./DEP/daf-guild-layer-flowchart.svg
    :width: 500

    Delovanje cehovskega nivoja

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

Glede na to da je ogrodje mišljeno kot neko ogrodje za oglaševanje sporočil, ta nivo nekako velja za najbolj glavnega.

.. Inicializacija |TextMESSAGE| in |VoiceMESSAGE| objektov poteka na sledeč način. Najprej preveri se podatkovni tip parametra
.. ``channels``, ki predstavlja kanale kamor se bo sporočila pošiljalo in sicer obstajajo 2 možnosti podatkovnega tipa:

.. 1. :class:`daf.message.AutoCHANNEL` - Je objekt, ki skrbi za avtomatično najdbo kanalov v cehu na podlagi nekega RegEx
..    vzorca, podobno kot |AutoGUILD| v :ref:`cehovskem nivoju <Cehovski nivo>`.
..    V tem primeru sporočilni nivo inicializira podani :class:`~daf.message.AutoCHANNEL` objekt.

.. 2. :class:`list` (seznam), *snowflake* identifikatorjev (tipa :class:`int`) ali pa objektov iz ovojnega API nivoja, ki so lahko
..    :class:`discord.TextChannel` za |TextMESSAGE| ali :class:`discord.VoiceChannel` za |VoiceMESSAGE| objekt.
..    Inicializacija gre čez celoten seznam in v primeru *snowflake* identifikatorja za ta identifikator poskusi najti pripadajoči
..    :class:`~discord.TextChannel` oz. :class:`~discord.VoiceChannel` objekt s tem identifikatorjem. Če pripadajočega
..    objekta ne najde, se v terminalu izpiše opozorilo in inicializacija se nadaljuje na ostalih elementih v seznamu.
..    V primeru neveljavnega tipa elementa v seznamu, inicializacija dvigne Python_ napako tipa :class:`TypeError`.
..    V primeru da identifikator pripada kanalu, ki pripada nekem drugemu cehu, kot je ceh v katerem se nahaja trenutni 
..    sporočilni objekt, inicializacija dvigne napako tipa :class:`ValueError`.

..    V primeru |TextMESSAGE| objekta se na koncu še preveri če je podana perioda pošiljanja manjša od minimalnega
..    čakanja počasnega načina (*Slow mode*) in periodo ustrezno popravi.


.. Inicializacija |DirectMESSAGE| objekta je precej bolj enostavna. Iz starša (|USER|) se pridobi objekt, ki na ovojnem API
.. nivoju predstavlja ceh in na tem objektu se kliče metoda :py:meth:`discord.User.create_dm`.
.. Metoda :py:meth:`~discord.User.create_dm` predstavlja analogijo na tekstovni kanal v cehu.


.. Medtem ko se inicializacija različnih vrst sporočilnih objektov razlikuje, je sama glavna logika večinoma enaka.
.. V cehovskem nivoju se od sporočilnega nivoja preko :py:meth:`~daf.message.TextMESSAGE._is_ready` metode preverja ali
.. je sporočilo pripravljeno za pošiljanje v slednjem primeru začne s procesom pošiljanja sporočila.

Na začetku je bil sporočilni nivo mišljen le za hrambo podatkov o sporočilu in definiranje časa pošiljanja,
vsa ostala logika pa je bila pristotna v cehovksem nivoju, in sicer se je dejansko tam definiralo kanale za pošiljanje.
Po nekaj premislekih, preizkušanju in mnenj uporabnikov pa je bila logika pošiljanja v kanal prestavljena v sporočilni nivo,
kar omogoča tudi, da se sporočilo pošlje v več različnih kanalov (v istem cehu) brez ustvarjanja novih sporočilnih objektov
kot ob prejšnji implementaciji, kjer se je kanale definiralo v cehovskih objektih.
Med možnostmi je bila tudi, da bi se za same kanale ustvarilo ločen nivo, a bi to zahtevalo še več
pisanja ob definiciji oglaševalske skripte brez neke dodane vrednosti in posledično je bila ta ideja zavržena.

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
Pred tem algoritmom, je za določanje časa pošiljanja bil v rabi preprost časovnik, ki se je ponastavil ob vsakem pošiljanju, a se je zaradi Discord-ove
omejitve API zahtevkov in tudi drugih Discord API zakasnitev, čas pošiljanja vedno pomikal malo naprej, kar je pomenilo, da če je uporabnik
ogrodje konfiguriral da se neko sporočilo pošlje vsak dan in definiral čas začetka naslednje jutro ob 10tih (torej pošiljanje vsak dan ob tej uri),
potem je po (sicer veliko) pošiljanjih namesto ob 10tih uporabnik opazil, da se sporočilo pošlje ob 10.01, 10.02, itd.
Primer časovne napake je prikazan na spodnji sliki.

.. figure:: ./DEP/daf-message-period.svg
    :width: 500

    Čas pošiljanja sporočila s toleranco zamud


.. Proces pošiljanja sporočila poteka tako, da sporočilni nivo najprej pridobi podatke za pošiljanje. Ti podatki so lahko
.. fiksni podatki podani ob kreaciji sporočilnega objekta, lahko pa se jih pridobi tudi dinamično v primeru, da je bila
.. ob kreaciji objekta podana funkcija. V slednjem primeru se funkcijo pokliče in v primeru da vrne veljaven tip podatka za
.. vrsto sporočilnega objekta, se ta podatek uporabi pri pošiljanju sporočila - glej :func:`daf.dtypes.data_function`.
.. Po pridobivanju podatkov, sporočilni objekt za vsak svoj kanal preveri ali je uporabnik:

.. - še pridružen cehu,
.. - ima pravice za pošiljanje,
.. - kanal še obstaja.

.. Če karkoli od zgornjega ni res, se dvigne ustrezna Python_ napaka, ki simulira napako ovojnega API nivoja.
.. Tip dvignjene napake je podedovan iz :class:`discord.HTTPException`.
.. V primeru, da ni bila dvignjena nobena napaka, se sporočilo pošlje v kanal. Če je sporočilni objekt tipa
.. .. |TextMESSAGE| ali |DirectMESSAGE|, se lahko na podlagi ``mode`` parametra sporočilo pošlje na različne načine.

.. Po poslanem sporočilu se podatke sporočila in status pošiljanja pošlje :ref:`cehovskem novoju <Cehovski nivo>`.

.. figure:: ./DEP/daf-message-process.svg
    :width: 800

    Proces sporočilnega nivoja


.. raw:: latex

    \newpage


Nivo beleženja
---------------
Nivo beleženja je zadolžen za beleženje poslanih sporočil oz. beleženje poskusov pošiljanja sporočil. Podatke, ki jih
mora zabeležiti dobi neposredno iz :ref:`cehovskega nivoja <Cehovski nivo>`. Beleži se tudi podatke o pridužitvi novih članov, če
je to konfigurirano v cehovskem novoju.

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

Pred JSON, CSV in SQL logiranjem se je vse beležilo v Markdown datoteke, kjer se je potem v primeru
pregleda s pravim orodjem, lahko podatke pregledovalo v lepo berljivem formatu, a je bila ta vrsta logiranja zamenjana
z JSON logiranjem.


.. figure:: ./DEP/daf-high-level-log.svg
    :width: 500

    Višji nivo beleženja

.. raw:: latex

    \newpage

JSON beleženje
~~~~~~~~~~~~~~~~~
Kot že prej omenjeno, je bilo JSON beleženje zamenja za Markdown format beleženja. Razlog za zamenjavo je morebitna
implementacija analitike, kar bi se v Markdown formatu težko implementiralo. V času pisanja je analitika na voljo le v
primeru SQL logiranja.

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
Za sam pregled poslanih sporočil to ni najbolj primren format, saj se vse shrani v eni datoteki, kjer za razliko od JSON
formata, tu ni več slojnih struktur.


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

Ta vrsta beleženja je bila pravzaprav narejena v okviru zaključne naloge za izbirni predmet Informacijski sistemi v 2. letniku.
Ker smo morali pri predmetu izpolnjevati neke zahteve, je bilo dosti stvari pisanih neposredno v SQL jeziku, a vseeno je bila že takrat
uporabljena že prej omenjena knjižnica :mod:`SQLAlchemy`. Zaradi določenih SQL zahtev (funkcije, procedure, prožilci, ipd.),
je bila ta vrsta logiranja možna le ob uporabi Microsoft SQL Server baze.
Kasneje se je postopoma celotno SQL kodo zamenjalo z ekvivalentno Python kodo, ki preko SQLAlchemy knjižnice dinamično
generira potrebne SQL stavke, zaradi česar so bile odstranjene določene uporabne originalne funkcionalnosti implementirane
na nivoju same SQL baze kot so npr. prožilci (angl. *trigger*). Je pa zaradi tega možno uporabljati bazo na večih dialektih,
tudi v SQLite, ki vse shranjuje lokalno v datoteki, dodatno pa je tudi konfiguracija precej lažja.



Spodnja slika prikazuje povezavo relacij (tabel) med seboj.
Celoten opis pa je na voljo v :ref:`dokumentaciji ogrodja <SQL Tables>`.

.. figure:: ./DEP/sql_er.drawio.svg
    :width: 500

    SQL entitetno-relacijski diagram


.. figure:: ./DEP/daf-logging-sql.svg
    :width: 500

    Proces beleženja z SQL podatkovno bazo


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
PyCord je odprtokodno ogrodje, ki je nastalo iz kode starejšega `discord.py <https://discordpy.readthedocs.io/en/stable/>`_.
Razlog da ga tu imenujem ogrodje, je da poleg tega da ponuja abstrakcijo Discord API, PyCord interno za vsak račun ustvari
tudi svoje :mod:`asyncio` opravilo, ki na podlagi dogodkov iz Discord "Gateway"-a (uradno ime) posodablja svoje objekte,
kot so :class:`~discord.TextChannel`, :class:`~discord.Guild`, :class:`~discord.User` in druge. Na primer, če bi imeli nekje
shranjen objekt :class:`discord.Guild` in bi pripadajočem cehu spremenili ime, bi se ta sprememba takoj poznala v 
:class:`~discord.Guild` objektu. Vsi objekti v Python_-u  se kopirajo po referenci, zato se spremembe poznajo na vseh kopijah.
Ogrodje PyCord skoraj popolnoma zakrije Discord API z raznimi objekti, ki jih DAF interno uporablja.

Če bi si ogledali izvirno kodo DAF, bi opazili da je poleg ``daf`` paketa zraven tudi paket z imenom ``_discord``.
To ni nič drugega, kot PyCord ogrodje, le da je modificirano za možnost rabe na osebnih uporabniških računih.
Poleg lokalnih modifikacij, sem tudi na uradni verziji PyCord ogrodja naredil nekaj, z namenom izboljšanje nekaterih
funkcionalnosti na DAF ogrodju.
Da bi PyCord ogrodje bilo možno posodabljati, so z ukazom ``git diff`` ustvarjene GIT datoteke za krpanje (*patch*),
kar pravzaprav omogoča da se novo verzijo PyCord ogrodja preprosto kopira v mapo in z ``git apply`` uvozi spremembe v
datotekah za krpanje.

Več je na voljo v `uradni PyCord dokumentaciji <https://docs.pycord.dev/en/stable/>`_.



Zasnova in razvoj grafičnega vmesnika
============================================
DAF lahko deluje popolnoma brez grafičnega vmesnika, a ta način zahteva pisanje *.py* datotek oz. Python skript, kar
ja marskikomu težje, sploh če se še nikoli niso srečali s Python jezikom.

V namen enostavnejše izkušnje pri uporabi ogrodja, obstaja grafični vmesnik, ki deluje ločeno od samega ogrodja, z njim pa
komunicira preko njegovih programskih funkcij.

.. figure:: ./DEP/daf-gui-front.png
    :width: 15cm

    Grafični vmesnik (privzet prikaz)

.. raw:: latex

    \newpage

Kot je razvidno iz gornje slike, je za dizajn vmesnika izbran svetel dizajn z modrimi odtenki za posamezne elemente.
Pred to temo je bila planira tema z turkiznimi barvami, vendar je ob odzivih uporabnikov trenuten dizajn prevladov.


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

Več o Tkinter knjižnici si lahko preberete na uradni Python dokumentaciji :mod:`tukaj <tkinter>`.

Pred izbiro te knjižnice je bila med možnosti tudi knjižnica PySide (QT), a na koncu je bila vseeno izbrana Tkinter
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

Uporabniške račune se lahko definira tako, da ob kliku na opcijski meni *Object options*, uporabniki izberejo opcijo *New ACCOUNT*.
Ob kliku se nam odpre novo okno, ki je avtomatično in dinamično generirano iz podatkov o podatkovnih tipih (anotacij), ki jih sprejme
razred ob definiciji. V oknu se za vsak parameter generira labela, opcijski meni in opcijski gumb, v katerem lahko urejamo izbrano vrednost
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


.. raw:: latex

    \newpage

Podobno se definira tudi upravljalnik za beleženje.


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




Dokumentacija
=========================

.. _Python: https://www.python.org


.. _restructuredText: https://docutils.sourceforge.io/rst.html

.. _RTD: https://readthedocs.org/projects/discord-advertisement-framework/

.. |RTD| replace:: Read The Docs


Za projekt obstaja obsežna dokumentacija. Na voljo je v spletni obliki (HTML), kot tudi
lokalni (PDF).

Za vsako novo verzijo projekta, se dokumentacija samodejno zgradi in objavi na `spletni strani <https://daf.davidhozic.com>`_.

Sphinx
----------------
Sistem, ki se uporablja za dokumentiranje projekta se imenuje Sphinx.
Sphinx je popularno orodje med Python_ razvijalci za generiranje dokumentacije v več formatih.
Razvijalcem omogoča ustvarjanje profesionalne dokumentacije za lastne projekte, kar je nuja pri javnih projektih.

Sphinx omogoča enostavno dokumentiranje z berljivo sintakso (restructuredText) z veliko funkcionalnostmi, kjer je ena izmed njih
možnost branja t.i *docstring* :class:`str` objektov iz kode projekta in vključevanju te vsebine v dokumentacijo.
Je zelo konfigurabilno orodje, kjer se konfiguracijo izvede preko ``.py`` datoteke, kamor lahko dodajamo tudi svojo
Python_ kodo.

Primarno Sphinx podpira restructuredText_ za pisanje dokumentov, podpira pa tudi ostale formate, npr. Markdown preko
dodatnih razširitev. Enačbe se lahko piše v jeziku Latex.

.. admonition:: Zanimivost
    :class: hint

    Ta diplomska naloge je pisana ravno s sistemom Sphinx.


reStructuredText
----------------

restructuredText je jezik na katerem deluje :ref:`Sphinx`.
Je priljubljen *markup* jezik, ki se uporablja za dokumentacijo.
Oblikovan je za enostavnost branja, z fokusom na preprostost in moč.
Ena ključnih značilnosti reStructuredTexta je njegova razširljivost, kar omogoča prilagajanje za specifična aplikacijska področja.

Znotraj sintakse reStructuredTexta so na voljo različne vloge in direktive, ki se uporabljajo za dodajanje oblikovanja in strukture dokumentom.
Vloge se uporabljajo za aplikacijo oblikovanja na določene besede in stavke,
direktive pa so uporabljene za dodajanje nove vsebine v dokument.
Uporabnikom omogočajo ustvarjanje bolj zapletenih in dokumentov,
pri tem pa ohranjajo preprostost in berljivost sintakse.


.. code-block:: reStructuredText
    :caption: reStructuredText direktiva

    .. figure:: img/rickroll.png
        :scale: 50%

        Rickroll image

    .. math:: 
        :label: Derivative of an integral with parameter
        
        \frac{d}{dy}(F(y))=\int^{g_2(y)}_{g_1(y)}f_y dx +
        (f(g_2(y), y)\cdot g_2(y)'{dy} - f(g_1(y), y)\cdot g_1(y)')


.. code-block:: reStructuredText
    :caption: reStructuredText vloga

    :math:`\int 1 dx = x + C`.
    If the above isn't hard enough, the 
    :eq:`Derivative of an integral with parameter`
    is a bit harder.


Dokumentacija projekta
--------------------------------
Projekt DAF je v celoti dokumentiran s Sphinx sistemom.
Na prvem nivoju je dokumentacija razdeljena na:

1. Vodnik - Voden opis kako uporabljati DAF.
2. API referenco - Opis vseh razredov in funkcij, ki jih lahko uporabniki uporabijo v primeru, da pišejo
   svojo kodo, ki uporablja DAF kot paket.

Vodnik je pisan v ``.rst`` datotekah, ki so nastanjene v ``docs/source/guide`` mapi. Dodatno se deli še na vodnik za
GUI in vodnik za jedro.

V nekaterih direktorijah so prisotne datoteke ``dep_local.json``. To so pred-gradne konfiguracijske datoteke, ki dajejo
informacijo o tem iz kje in kam naj se kopirajo dodatne datoteke (ki so skupne drugim delom dokumentacije) in katere
``.py`` skripte naj se izvedejo po kopiranju.
Na primer ``/project root/docs/source/dep_local.json`` datoteka ima sledečo vsebino:

.. literalinclude:: DEP/_dep_local.json
    :caption: Pred-gradna konfiguracijska datoteka

Na podlagi zgornje definicije, se bo bodo v ./DEP mape skopirale slike iz neke zgornje direktorje. Prav tako
se bodo kopirali primeri uporabe jedra DAF. Na koncu se bo izvedla skripta ``generate_autodoc.py``, ki bo na podlagi
:func:`~daf.misc.doc_category` Python_ dekoratorja generirala ``autofunction`` in ``autoclass`` Sphinx direktive, ki bodo
ob gradnji dokumentacije prebrale vsebino *docstring*-ov posameznih razredov in funkcij, ter jo vstavile v dokument.
V primeru da bo ``manual`` parameter nastavljen na ``True`` v 
:func:`~daf.misc.doc_category` dekoratorski funkciji, ne bodo generirane ``autofunction`` direktive, temveč bo skripta
ustvarila ``function`` direktive ter vsebino prekopirala in pretvorila direktno v ``.rst`` datoteko.


.. autofunction:: daf.misc.doc_category


.. code-block:: python
    :caption: Uporaba :func:`~misc.doc_category` dekoratorja.

    @misc.doc_category("Logging reference", path="logging.sql")
    class LoggerSQL(logging.LoggerBASE):
        ...


Generirane ``autofunction`` / ``autoclass`` direktive so del Sphinx-ove vgrajene razširitve :mod:`sphinx.ext.autodoc`.
Razširitev vključi pakete in izbrska *docstring*-e funkcij in razredov, zatem pa ustvari lep opis o funkciji oz. razredu.
V primeru da je v ``autoclass`` direktivi uporabljena ``:members:`` opcija, bo :mod:`~sphinx.ext.autodoc` razširitev
vključila tudi dokumentirane metode in atribute, ki so del razreda.

.. code-block:: restructuredText
    :caption: Avtomatično generirana API referenca

    ============================
    Dynamic mod.
    ============================

    ------------------------
    add_object
    ------------------------
    
    .. Uporabljen je bil manual parameter v doc_category
    .. function:: daf.core.add_object(obj: <class 'daf.client.ACCOUNT'>) -> None
        
        Adds an account to the framework.
        
        
        :param obj: The account object to add
        :type obj: client.ACCOUNT
        
        
        :raises ValueError: The account has already been added to the list.
        :raises TypeError: ``obj`` is of invalid type.


    ============================
    Clients
    ============================

    ------------------------
    ACCOUNT
    ------------------------

    .. autoclass:: daf.client.ACCOUNT
        :members:


Rezultat gornje vsebine:

.. figure:: ./DEP/autodoc_example.png
    :height: 140mm

    Izhod avtomatično generirane API reference.

Iz gornje slike vidimo, da ima :class:`~daf.client.ACCOUNT` dodatno vsebino, ki je ni imel v ``autoclass`` direktivi.
Ta vsebina je bila vzeta iz kode projekta DAF, ki ima sledečo definicijo:

.. code-block:: python
    :caption: Del definicije razreda :class:`~daf.client.ACCOUNT`

    class ACCOUNT:
        """
        .. versionadded:: v2.4

        Represents an individual Discord account.
        
        Each ACCOUNT instance runs it's own shilling task.

        Parameters
        ----------
        token : str
            The Discord account's token
        is_user : Optional[bool] =False
            Declares that the ``token`` is a user account token
            ("self-bot")
        intents: Optional[discord.Intents]=discord.Intents.default()
            Discord Intents
            (settings of events that the client will subscribe to)
        ...
        """
        ...

        @property
        def running(self) -> bool:
            """
            Is the account still running?

            Returns
            -----------
            True
                The account is logged in and shilling is active.
            False
                The shilling has ended or not begun.
            """
            ...

        ...

        @typechecked
        def get_server(
            self,
            snowflake: Union[int, discord.Guild, discord.User, discord.Object]
        ) -> Union[guild.GUILD, guild.USER, None]:
            """
            Retrieves the server based on the snowflake id or discord API object.

            Parameters
            -------------
            snowflake: Union[int, discord.Guild, discord.User, discord.Object]
                Snowflake ID or Discord API object"
            ...
            """
            ...

        ...


Dokumentacija projekta DAF je na voljo na spletni strani `Read the Docs (RTD) <RTD_>`_.

RTD_ je spletna platforma za dokumentacijo, ki razvijalcem programske opreme zagotavlja enostaven način za gostovanje,
objavljanje in vzdrževanje dokumentacije za njihove projekte.
Platforma uporabnikom omogoča ustvarjanje profesionalno izgledajoče dokumentacije, ki je odprta javnosti.
Je odprtokodna in zgrajena na že prej omenjenem Sphinx-u.

Poleg gostovanja dokumentacije RTD_ ponuja razna orodja, kot so orodje za nadzor različic in napredna funkcionalnost iskanja.
To uporabnikom olajša lažji pregled dokumentacije in zagotavlja, da dokumentacija ostane ažurna.

RTD_ je za DAF projekt konfiguriran, da za vsako novo izdajo verzije preko platforme GitHub, avtomatično zgradi dokumentacijo,
aktivira verzijo in jo nastavi kot privzeto. Na tak način je dokumentacija pripravljena za uporabo praktično takoj ob izdaji verzije.



Avtomatično testiranje
=============================

.. _PyTest: https://docs.pytest.org/

Za zagotavljanje, da ob novih verzijah projekta ne pride do napak, ko spreminjamo funkcionalnost, je za preverjanje delovanja
implementirano avtomatično testiranje (*Unit testing*).

Vsi avtomatični testi so pisani znotraj ogrodja za testiranje z imenom Pytest_.


PyTest - ogrodje za testiranje
-------------------------------------
Kot že ime namiguje, je PyTest orodje za testiranje na Python platformi.
PyTest-ova sintaksa je enostavna za razumevanje in uporabo, tudi za tiste ki se s avtomatičnim testiranjem
še niso ukvarjali.

Avtomatične teste se pri PyTestu implementira z navadnimi funkcijami, ki se začnejo z "test".
Testi lahko kot parametre sprejmejo tudi
tako imenovane (angl.) *Fixture* -je , ki jih lahko uporabimo kot pred-testne inicializacijske funkcije.
V fixture lahko npr. povežemo podatkovno bazo, konektor na bazo vrnemo iz fixture funkcije, in 
v primeru da je naš test definiran kot

.. code-block:: python

    @pytest.mark.asyncio
    async def test_moje_testiranje(ime_fixture):
        ...

bo naš test prejel vrednost, ki jo je fixture ``ime_fixture`` vrnil. Fixture ima lahko različno dolgo življensko dobo,
kar pomeni da bo lahko več testov prejelo isto vrednost, ki jo je fixture vrnil dokler se življenska doba ne izteče.
Fixture je lahko tudi `Python generator <https://wiki.python.org/moin/Generators>`_, kar nam omogoča inicializacijo testov in 
čiščenje na koncu na sledeč način:

.. code-block:: python
    :caption: PyTest fixture, ki obstaja življenjsko dobo vseh testov.
    
    @pytest_asyncio.fixture(scope="session")
    def ime_fixture(ime_nek_drug_fixture):
        # Inicializacija
        database = DataBaseConnector()
        database.connect("svet.fe.uni-lj.si/api/database")

        yield database  # Vrednost, ki jo dobijo testi

        # Čiščenje po testih
        database.disconnect()
        database.cleanup()



Preverjanje ali je test uspel se izvede s stavkom ``assert``, ki dvigne :class:`AssertionError` napako, v primeru
da njegova vhodna vrednost ni enaka ``True``.
V primeru da je dvignjen :class:`AssertionError`, PyTest zabeleži test kot neuspel in izpiše napako.
In izpiše kaj je šlo narobe. Kako podroben bo izpis, se lahko nastavi ob zaganjanju testa, npr.
``pytest -vv``, kjer ``-vv`` nastavi podrobnost. Kot primer si poglejmo kaj bo izpisal, če v assert stavek
kot vhod damo primerjavo dveh seznamov.

.. code-block:: python
    :caption: Primerjava dveh :class:`seznamov <list>`, ki nista enaka

    assert [1, 2, 3] == [1, 2, 3, 4, 5, 6]


Iz zgornjega testa je očitno da to ne drži in da bo test neuspel, ampak v assertu nimamo nobenega
izpisa, ki kaj izpisal, tako da bi pričakovali da PyTest vrne samo informacijo da test ni uspel.
PyTest je bolj pameten, kot to in sicer nam bo izpisal točno kateri elementi se v seznamu razlikujejo.

.. code-block::
    :caption: PyTest izpis ob neuspelem testu pri primerjavi dveh :class:`seznamov <list>`.

    ========================================================= test session starts =============
    platform win32 -- Python 3.8.10, pytest-7.2.0, pluggy-1.0.0 -- C:\dev\git\discord-advert    
    cachedir: .pytest_cache
    rootdir: C:\dev\git\discord-advertisement-framework
    plugins: asyncio-0.20.3, typeguard-2.13.3
    asyncio: mode=strict
    collected 1 item

    test.py::test_test FAILED                                           [100%]

    =============================================================== FAILURES =================== 
    ______________________________________________________________ test_test ___________________

        def test_test():
    >       assert [1, 2, 3] == [1, 2, 3, 4, 5, 6]
    E       assert [1, 2, 3] == [1, 2, 3, 4, 5, 6]
    E         Right contains 3 more items, first extra item: 4
    E         Full diff:
    E         - [1, 2, 3, 4, 5, 6]
    E         + [1, 2, 3]

    test.py:6: AssertionError


Testiranje ogrodja
---------------------
Testi so v ogrodju DAF razdeljeni po posameznih nivojih in funkcionalnosti. Skoraj vsi testi delujejo sinhrono,
tako da se v testu kliče notranje funkcije posameznih objektov, ki bi jih ogrodje
samo klicalo v primeru navadnega delovanja. To je zato ker je testiranje v navadnem načinu, kjer se vse
zgodi v :mod:`asyncio` opravilih, težko testirati. Namreč morali bi loviti ogrodje točno ob določenih časih, da
bi dejansko testirali to kar želimo.
Kljub temu, obstajata dva testa, ki ogrodje poženeta v navadnem načinu, in sicer to sta testa, ki testirata če
je perioda pošiljanja prava in vzporedno preverjata tudi delovanje dinamičnega pridobivanja podatkov.
Kot sem že prej omenil, je pri teh dveh testih potrebna uloviti pravi čas, zato se včasih pojavijo problemi
z Discord-ovim omejevanjem hitrosti na API klice, kar lahko povzroči da bo pri pošiljanju sporočila ovojni API nivo,
rabil več časa da naredi zahtevo na API, saj bo čakal da se omejitev izteče. V tem primeru bo PyTest izpisal, da test
ni uspel in ga je potrebno ponoviti. Vsi testi se nahajajo v mapi ./testing relativno na dom projekta.

Avtomatičnih testov običajno ne zaganjam ročno na osebnem računalniku, razen tistih, ki so preverjajo delovanje neke
nove funkcionalnosti, temveč se na GitHub platformi avtomatično zaženejo ob vsakem zahtevku za združitev vej (*Pull request*), ko hočem funkcionalnost
iz stranske git veje prenesti na glavno. Dokler se vsi testi ne izvedejo pravilno (in avtomatičen *linter* vrača lepotne napaka),
GitHub ne bo pustil da se funkcionalnost prenese na glavno vejo.

