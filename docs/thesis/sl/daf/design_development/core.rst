=========================
Zasnova in razvoj jedra
=========================

.. _Python: https://www.python.org

.. |USER| replace:: :class:`~daf.guild.USER`
.. |GUILD| replace:: :class:`~daf.guild.GUILD`
.. |AutoGUILD| replace:: :class:`~daf.guild.AutoGUILD`

.. |TextMESSAGE| replace:: :class:`~daf.message.TextMESSAGE`
.. |VoiceMESSAGE| replace:: :class:`~daf.message.VoiceMESSAGE`
.. |DirectMESSAGE| replace:: :class:`~daf.message.DirectMESSAGE`
.. |AutoCHANNEL| replace:: :class:`~daf.message.AutoCHANNEL`

.. |TOPGG| replace:: https://top.gg


To poglavje govori o jedru samega ogrodja, kjer jedro obsega vse, kar ni del grafičnega vmesnika.

Jedro DAF-a je zasnovano kot Python_ knjižnica / paket, ki se ga lahko namesti preko PIP-a (*Preferred Installer Program*), ki je
vgrajen v Python_ in služi nalaganju Python paketov. Za uporabo jedra morajo uporabniki ustvariti ``.py`` datoteko in definirati
ustrezno konfiguracijo. To zahteva nekaj osnovnega znanja Python jezika, obstaja pa tudi možnost, da se to datoteko
generira iz grafičnega vmesnika (:ref:`Zasnova in razvoj grafičnega vmesnika`)

Za lažjo implementacijo in kasnejši razvoj, je jedro DAF ogrodja razdeljeno na več nivojev abstrakcije oziroma plasti.
Ti nivoji so:

- Nadzorni nivo
- Uporabniški nivo
- Cehovski (strežniški) nivo
- Sporočilni nivo
- Nivo beleženja zgodovine
- Nivo brskalnika (Selenium)
- Ovojni nivo Discord API


.. figure:: ./DEP/daf_abstraction.drawio.svg

    Abstrakcija jedra ogrodja


.. raw:: latex

    \newpage


Nadzorni nivo
---------------------
Nadzorni nivo skrbi za zagon samega ogrodja ter njegovo zaustavitev. Skrbi tudi za procesiranje ukazov, ki jih DAF ponuja
preko lastnega programskega vmesnika ali preko HTTP vmesnika, kjer v programski vmesnik spadajo Python funkcije ogrodja in metode objektov
za neposredno upravljanje ogrodja na isti napravi, v HTTP vmesnik pa spletne HTTP poti za upravljanje na daljavo.
Nivo služi tudi odstranjevanju neuporabljenih objektov in skrbi za prezervacijo uporabniških računov ob izklopu.

Ko zaženemo ogrodje, ta v nadzornem nivoju sproži inicializacijo nivoja beleženja in zatem uporabniškega nivoja,
kjer za vsak definiran uporabniški račun ustvari lastno :mod:`asyncio` opravilo,
kar omogoča asinhrono sočasno oglaševanje po več računih hkrati.
Na koncu pokliče (s strani uporabnika definirano) funkcijo, ki je bila podana kot parameter ob klicu zaganjalne funkcije :func:`daf.core.run`.

Nadzorni nivo ima vedno vsaj eno opravilo (poleg opravil v ostalih nivojih), in sicer je to tisto, ki skrbi za čiščenje uporabniških računov v primeru napak.
Drugo opravilo se zažene le v primeru, da je vklopljeno shranjevanje objektov v datoteko (preko :func:`~daf.core.run` funkcije).
Ogrodje samo po sebi deluje tako, da ima vse objekte (račune, cehe, sporočila, ipd.) shranjene kar neposredno v RAM pomnilniku.
Že od samega začetka je ogrodje narejeno na način, da se željene objekte definira kar preko Python skripte in je zato shranjevanje v RAM
ob taki definiciji neproblematično, problem pa je nastopil, ko je bilo dodano dinamično dodajanje in brisanje objektov, kar
dejansko uporabnikom omogoča, da ogrodje dinamično uporabljajo in v tem primeru je bilo potrebno dodati neke vrste permanentno shrambo.
Razmišljalo se je o več alternativah, ena izmed njih je bila da bi se vse objekte shranjevalo v neko bazo podatkov, ki bi omogočala
mapiranje podatkov v bazi, kar bi z vidika robustnosti bila zelo dobra izbira, a to bi zahtevalo veliko prenovo
vseh nivojev, zato se je na koncu izbrala preprosta opcija shranjevanja objektov, ki preko :mod:`pickle` modula shrani vse račune
ob vsakem normalnem izklopu ogrodja, ali pa v vsakem primeru na dve minuti periodično. V prihodnosti so
še vedno načrti za izboljšanje tega mehanizma in ne izključuje se uporaba prej omenjene podatkovne baze.

V nadzornem novoju se (poleg programskega vmesnika) nahaja tudi tudi HTTP vmesnik, ki služi kot
podpora za oddaljen dostop grafičnega vmesnika do jedra. Deluje na knjižnici `aiohttp <https://docs.aiohttp.org/en/stable/index.html>`_, ki je asinhrona
HTTP knjižnica.
HTTP vmesnik je v resnici zelo preprost in deluje tako, da ob neki HTTP zahtevi ustvari novo :mod:`asyncio` opravilo,
ki potem zahtevo posreduje programskemu vmesniku, kar pomeni da je rezultat enak tistemu, ki bi ga dobili ob lokalnem delovanju na isti napravi.
Vsi podatki se na HTTP vmesniku pretakajo v :term:`JSON` formatu (kompresiranem z :mod:`gzip`).
Osnoven koncept je prikazan na spodnji sliki.


.. _gui-core-connection:
.. figure:: ./DEP/daf-core-http-api.drawio.svg

    Povezava do jedra (barve puščic prikazujejo ločen potek)


Računski nivo
---------------
Računski nivo je zadolžen za upravljanjem z uporabniškimi računi. Vse kar se dogaja v tem nivoju se zgodi preko
:class:`daf.client.ACCOUNT` objekta.

Računski nivo skrbi za inicializacijo nivoja, ki ovija Discord API in za upravljanje opravila, ki komunicira z cehovskim nivojem.


.. figure:: ./DEP/daf-account-layer-flowchart.svg
    :width: 500

    Delovanje računskega nivoja



Cehovski nivo
---------------
Cehovski nivo je primarno zadolžen za upravljanje s cehi in komuniciranje s sporočilnim nivojem. V primeru
naprednejših funkcionalnosti, kot je avtomatično pridruževanje cehom, komunicira tudi z nivojem brskalnika.

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
ne samo notranje kode, ampak tudi kode za definiranje same oglaševalske skripte ob velikem številu sporočil.
To je sicer posledično zahtevalo definicijo dodatnih vrstic v oglaševalski skripti, kar je hitro postalo opazno ob 90tih različnih cehih.
Vseeno se je ta izbira dobro izšla, saj je zdaj na cehovskem nivoju veliko funkcionalnosti, ki ne spada v ostale nivoje, 
kot je na primer avtomatično iskanje novih cehov, in njihovo pridruževanje. Ta abstrakcija nudi tudi veliko preglednosti
v primeru logiranja (vsaj v primeru :term:`JSON` datotek), kjer je vse razdeljeno po različnih cehih.


.. figure:: ./DEP/daf-guild-layer-flowchart.svg
    :width: 20cm

    Delovanje cehovskega nivoja


.. raw:: latex

    \newpage


Sporočilni nivo
-----------------
Sporočilni nivo je zadolžen za pošiljanje dejanskih sporočil v posamezne kanale na Discordu.
V tem nivoju so na voljo trije glavni razredi za ustvarjanje različnih vrst sporočil:

1. |TextMESSAGE| - pošiljanje tekstovnih sporočil v cehovske kanale
2. |VoiceMESSAGE| - predvajanje posnetkov v cehovskih kanalih
3. |DirectMESSAGE| - pošiljanje tekstovnih sporočil v direktna (zasebne) kanale neposredno uporabnikom.


|TextMESSAGE| in |DirectMESSAGE| sta si precej podobna, primarno gre v obeh primerih za tekstovna sporočila, razlika
je v kanalih, ki jih |DirectMESSAGE| nima, temveč ta pošilja sporočila v direktna sporočila uporabnika.
|VoiceMESSAGE| in |TextMESSAGE|, sta si po vrsti podatkov sicer različna, vendar pa oba pošiljata sporočila v kanale, ki
pripadata nekemu cehu in imata praktično enako inicializacijo.

Glede na to da je ogrodje mišljeno za oglaševanje sporočil, ta nivo nekako velja za najbolj glavnega.

Pripravljenost sporočila za pošiljanje določa notranji atribut objekta, ki predstavlja točno specifičen čas naslednjega
pošiljanja sporočila. V primeru da je trenutni čas večji od tega atributa, je sporočilo pripravljeno za pošiljanje.
Ob ponastavitvi "časovnika" se ta atribut prišteje za konfigurirano periodo.
Torej čas pošiljanja ni relativen na dejanski prejšnji čas pošiljanja, temveč je relativen na predvideni prejšnji čas pošiljanja.
Taka vrsta računanja časa omogoča določeno toleranco pri pošiljanju sporočila, saj se zaradi raznih zakasnitev in omejitev
zahtev (angl. *Rate limiting*) na Discord API dejansko sporočilo lahko pošlje kasneje kot predvideno.
To je še posebno pomembno v primeru da imamo definiranih veliko sporočil v enem računu, kar je zagotovilo da se sporočilo ne bo
poslalo točno ob določenem času. Ker se čas prišteva od prejšnjega predvidenega časa pošiljanja, to pomeni, da bo v primeru
zamude sporočila razmak med tem in naslednjim sporočilom manjši točno za to časovno napako (če privzamemo da ne bo ponovne zakasnitve).

Pred tem algoritmom, je za določanje časa pošiljanja bil v rabi preprost časovnik, ki se je ponastavil ob vsakem pošiljanju, a se je zaradi Discordove
omejitve API zahtevkov in tudi drugih Discord API zakasnitev, čas pošiljanja vedno pomikal malo naprej, kar je pomenilo, da če je uporabnik
ogrodje konfiguriral da se neko sporočilo pošlje vsak dan in definiral čas začetka naslednje jutro ob 10tih (torej pošiljanje vsak dan ob tej uri),
potem je po (sicer veliko) pošiljanjih namesto ob 10tih uporabnik opazil, da se sporočilo pošlje ob 10.01, 10.02, itd.
Primer računanja časa in odprave časovne napake je prikazan na spodnji sliki.

.. figure:: ./DEP/daf-message-period.svg
    :width: 500

    Čas pošiljanja sporočila s toleranco zamud


.. figure:: ./DEP/daf-message-process.svg

    Proces sporočilnega nivoja


.. raw:: latex

    \newpage


Nivo beleženja
---------------
Nivo beleženja je zadolžen za beleženje poslanih sporočil oz. beleženje poskusov pošiljanja sporočil. Podatke, ki jih
mora zabeležiti dobi neposredno iz :ref:`cehovskega nivoja <Cehovski nivo>`. Beleži se tudi podatke o pridužitvi novih članov, če
je to konfigurirano v cehovskem novoju.

DAF omogoča beleženje v tri različne formate, kjer vsakemu pripada lasten objekt beleženja:

1. :term:`JSON` - :class:`~daf.logging.LoggerJSON`
2. :term:`CSV` (nekatera polja so JSON) - :class:`~daf.logging.LoggerCSV`
3. :term:`SQL` - :class:`~daf.logging.sql.LoggerSQL`


Ob inicializaciji, se v nadzornem nivoju poda željen objekt beleženja, ki se inicializira in shrani v nivo beleženja.
Po svoji lastni inicializaciji, se inicializira še njegov nadomestni (``fallback`` parameter)
objekt, ki se uporabi v primeru kakršne koli napake pri beleženju.

Po vsakem poslanem sporočilu se iz cehovskega nivoja naredi zahteva, ki vsebuje podatke o cehu, poslanem sporočilu oz.
poskusu pošiljanja ter podatki o uporabniškem računu, ki je sporočilo poslal. Nivo beleženja posreduje zahtevo
izbranem objektu beleženja, ki v primeru napake dvigne Python_ napako (*exception*), na kar nivo beleženja 
reagira tako, da začasno zamenja objekt beleženja na njegov nadomestek in spet poskusi. Poskuša dokler mu ne
zmanjka nadomestkov ali pa je beleženje uspešno.

Pred JSON, CSV in SQL beleženjem se je vse beležilo v Markdown datoteke, kjer se lahko podatke pregledovalo v berljivem formatu,
vendar je bila ta vrsta beleženja kasneje zamenjana z JSON beleženjem.


.. figure:: ./DEP/daf-high-level-log.svg
    :width: 500

    Višji nivo beleženja

.. raw:: latex

    \newpage

JSON beleženje
~~~~~~~~~~~~~~~~~
Kot že prej omenjeno, je :term:`JSON` beleženje zamenjava za Markdown format beleženja. Razlog za zamenjavo je morebitna
implementacija analitike, kar bi se v Markdown formatu težko implementiralo. V času pisanja je analitika na voljo le v
primeru SQL beleženja.

JSON beleženje je implementirano z objektom beleženja :class:`~daf.logging.LoggerJSON`.
Ta vrsta beleženja nima nobene specifične inicializacije, kliče se le inicializacijska metoda njegovega morebitnega
nadomestka.

Ob zahtevi beleženja objekt :class:`~daf.logging.LoggerJSON` najprej pogleda trenuten datum, iz katerega tvori
končno pot do datoteke od (v parametrih) konfigurirane osnovne poti. Končna pot je določena kot ``Leto/Mesec/Dan/<Ime Ceha>.json``.

To pot, v primeru da ne obstaja, ustvari in zatem z uporabo vgrajenega Python_ modula :mod:`json` podatke shrani v
datoteko. Specifike so opisane v :ref:`Logging (core)`.


.. figure:: ./DEP/daf-logging-json.svg
    :width: 250

    Process JSON beleženja

.. raw:: latex

    \newpage

CSV beleženje
~~~~~~~~~~~~~~~~~~
:term:`CSV` beleženje deluje na enak način kot :ref:`JSON beleženje`. Edina razlika je v formatu, kjer je format tu CSV.
Lokacija datotek je enaka kot pri :ref:`JSON beleženje`. Za shranjevanje je uporabljen vgrajen Python_ modul :mod:`csv`.

Za sam pregled poslanih sporočil to ni najbolj primren format, saj se vse shrani v eni datoteki, kjer za razliko od JSON
formata, tu ni več-slojnih strukture.


SQL beleženje
~~~~~~~~~~~~~~~~~~
:term:`SQL` beleženje pa deluje precej drugače, kot delujeta :ref:`JSON beleženje` in :ref:`CSV beleženje`, saj se podatki shranjujejo
v podatkovno bazo, ki je v primeru uporabe SQLite dialekta lahko tudi datoteka.

Beleženje je omogočeno v štirih SQL dialektih:

1. SQLite
2. Microsoft SQL Server
3. PostgreSQL
4. MySQL / MariaDB

Za čim bolj univerzalno implementacijo na vseh dialektih, je bila pri razvoju uporabljena knjižnica :mod:`SQLAlchemy`.
Celoten sistem SQL beleženja je implementiran s pomočjo :term:`ORM`, kar med drugim omogoča tudi
da SQL tabele predstavimo z Python_ razredi, posamezne vnose v bazo podatkov oz. vrstice pa predstavimo z instancami
teh razredov. Z ORM lahko skoraj v celoti skrijemo SQL in delamo neposredno z Python_ objekti, ki so lahko tudi gnezdene
strukture, npr. vnosa dveh ločenih tabel lahko predstavimo z dvema ločenima instancama, kjer je ena instanca 
gnezdena znotraj druge instance.

Ta vrsta beleženja je bila pravzaprav narejena v okviru zaključnega projekta, pri predmetu Informacijski sistemi v 2.letniku.
Ker smo morali pri predmetu izpolnjevati določene zahteve, je bilo veliko stvari pisanih neposredno v SQL jeziku, a vseeno je bila že takrat
uporabljena knjižnica SQLAlchemy. Zaradi določenih SQL zahtev (funkcije, procedure, prožilci, ipd.),
je bila ta vrsta beleženja možna le ob uporabi Microsoft SQL Server dialekta.
Kasneje se je postopoma celotno SQL kodo zamenjalo z ekvivalentno Python kodo, ki preko SQLAlchemy knjižnice dinamično
generira potrebne SQL stavke, zaradi česar so bile odstranjene določene uporabne originalne funkcionalnosti implementirane
na nivoju same SQL baze, kot so npr. prožilci (angl. *trigger*), ki se jih da predstavljati kot neke odzivne funckije na dogodke.
Je pa zaradi tega možno uporabljati bazo na večih dialektih, dodatno pa je bilo veliko stvari lažje implementirati, saj se ni
potrebno zanašati na specifike dialekta.


.. figure:: ./DEP/sql_er.drawio.svg

    :ref:`SQL entitetno-relacijski diagram <SQL Tables>`


.. raw:: latex

    \newpage


Nivo brskalnika (Selenium)
-------------------------------
Velika večina DAF deluje na podlagi ovojnega API nivoja, kjer ta direktno komunicira z Discord API.
Določenih stvari pa se neposredno z Discord API ne da narediti ali pa za izvedbo neke operacije (prepovedane v pogojih uporabe)
obstaja velika možnost, da Discord suspendira uporabnikov račun.

Za ta namen je bil ustvarjen nivo brskalnika, kjer DAF namesto z Discord API, komunicira z brskalnikom
Google Chrome. To opravlja s knjižnico `Selenium <https://www.selenium.dev/>`_, ki je namenjena avtomatizaciji brskalnikov
in se posledično uporablja tudi kot orodje za avtomatično testiranje spletnih grafičnih vmesnikov.

V DAF projektu Selenium ni uporabljen za testiranje, temveč je uporabljen za avtomatično prijavljanje v Discord z uporabniškim
imenom in geslom, in pa za pol-avtomatično pridruževanje cehom. Za uporabo tega nivoja, je potrebno objektu :class:`~daf.client.ACCOUNT`
ob ustvarjanju podati uporabniško ime in geslo namesto žetona. Znotraj :class:`~daf.client.ACCOUNT` objekta se bo potem samodejno
ustvaril nanj vezanj objekt :class:`~daf.web.SeleniumCLIENT`.

.. figure:: ./DEP/daf-selenium-layer.svg

    Delovanje brskalniškega nivoja


.. raw:: latex

    \newpage


Ovojni Discord API nivo
-----------------------------
Nivo, ki ovija Discord API ni striktno del samega ogrodja, ampak je to knjižnica oz. ogrodje `Pycord <https://docs.pycord.dev/en/stable/>`_.
PyCord je odprtokodno ogrodje, ki je nastalo iz kode starejšega `discord.py <https://discordpy.readthedocs.io/en/stable/>`_.
Ogrodje PyCord skoraj popolnoma zakrije Discord API z raznimi objekti, ki jih DAF interno uporablja.

Če bi si ogledali izvorno kodo (angl. *source code*) DAF ogrodja, bi opazili da je poleg ``daf`` paketa zraven tudi paket z imenom ``_discord``.
To ni nič drugega kot PyCord ogrodje, le da je modificirano za možnost rabe na osebnih uporabniških računih.

Več je na voljo v `uradni PyCord dokumentaciji <https://docs.pycord.dev/en/stable/>`_.

.. raw:: latex

    \blankpage


