=========================
Zasnova in razvoj jedra
=========================

.. |USER| replace:: :class:`~daf.guild.USER`
.. |GUILD| replace:: :class:`~daf.guild.GUILD`
.. |AutoGUILD| replace:: :class:`~daf.guild.AutoGUILD`

.. |TextMESSAGE| replace:: :class:`~daf.message.TextMESSAGE`
.. |VoiceMESSAGE| replace:: :class:`~daf.message.VoiceMESSAGE`
.. |DirectMESSAGE| replace:: :class:`~daf.message.DirectMESSAGE`
.. |AutoCHANNEL| replace:: :class:`~daf.message.AutoCHANNEL`

.. |TOPGG| replace:: https://top.gg


To poglavje govori o jedru samega ogrodja, kjer jedro obsega vse, kar ni del grafičnega vmesnika.

Jedro je zasnovano kot Python knjižnica/paket, ki se ga lahko namesti preko PIP-a (*Preferred Installer Program*), ki je
vgrajen v Python in služi nalaganju Python paketov. Za uporabo jedra morajo uporabniki ustvariti oglaševalsko (konfiguracijsko)
``.py`` datoteko in definirati ustrezno konfiguracijo. To zahteva nekaj osnovnega znanja Python jezika, obstaja pa tudi možnost, 
da se to datoteko generira iz grafičnega vmesnika (:ref:`Zasnova in razvoj grafičnega vmesnika`).


AsyncIO
===============
Jedro ogrodja je zasnovano za sočasno (angl. *concurrent*) večopravilnost, kar pomeni, da se lahko na videz več opravil izvaja naenkrat, v
resnici pa se med njimi zelo hitro preklaplja. To je omogočeno s knjižnico :mod:`asyncio`.
AsyncIO omogoča ustvarjanje ``async`` funkcij, ki vrnejo korutine (angl. *coroutine*). Te korutine lahko potem zaženemo v opravilih,
med katerimi bo program preklopil vsakič, ko v trenutnem opravilu z ``await`` besedo na primer čakamo:

- konec neke asinhrone komunikacije (angl. *Async I/O*),
- da se trenutno opravilo zbudi iz spanja,
- da se nek semafor odklene [#asyncio_semaphore]_,
- ipd.

.. [#asyncio_semaphore] Semafor je mehanizem za sinhronizacijo opravil, kjer omejimo, koliko opravil lahko naenkrat dostopa do nekega zaščitenega
   dela kode oz. skupne surovine. https://docs.python.org/3/library/asyncio-sync.html.



.. raw:: latex

    \newpage


Sektorji jedra ogrodja
========================

Za lažjo implementacijo in kasnejši razvoj je jedro ogrodja razdeljeno na več sektorjev.
Ti so:

- nadzorni sektor,
- sektor uporabniških računov,
- cehovski (strežniški) sektor,
- sporočilni sektor,
- sektor beleženja zgodovine sporočil,
- sektor (avtomatizacije) brskalnika,
- sektor za ovoj Discord API (angl. *Discord API wrapper sector*).


.. figure:: ./DEP/daf_abstraction.drawio.svg

    Sestava jedra ogrodja

.. raw:: latex

    \newpage

Nadzorni sektor
---------------------
Nadzorni sektor skrbi za zagon samega ogrodja in njegovo zaustavitev. Skrbi tudi za procesiranje ukazov, ki jih ogrodje ponuja,
preko lastnega programskega vmesnika ali preko HTTP vmesnika, pri čemer v programski vmesnik spadajo Python funkcije ogrodja in metode objektov
za neposredno upravljanje ogrodja na isti napravi, HTTP vmesnik pa nudi podporo za upravljanje jedra na daljavo.

V tem sektorju se dodajajo novi uporabniški računi oz. se odstranjujejo tisti, v katerih je prišlo do napake.
Prav tako se tu zgodi inicializacija sektorja beleženja sporočil, s katerim kasneje komunicira cehovski sektor.


Nadzorni sektor ima vedno vsaj eno opravilo (poleg opravil v ostalih sektorjih), in sicer je to tisto, ki skrbi za čiščenje uporabniških računov v primeru napak.
Drugo opravilo se zažene le v primeru, da je vklopljeno shranjevanje objektov v datoteko.
Ogrodje samo po sebi deluje tako, da ima vse objekte (račune, cehe, sporočila ipd.) shranjene neposredno v RAM.
Že od samega začetka je ogrodje narejeno na način, da se želene objekte definira preko Python skripte in je zato shranjevanje v RAM
ob taki definiciji neproblematično, problem pa je nastopil, ko je bilo dodano dinamično dodajanje in brisanje objektov, kar
uporabnikom dejansko omogoča, da ogrodje uporabljajo dinamično. V tem primeru je bilo potrebno dodati neke vrste permanentno shrambo.
Razmišljalo se je o več alternativah, ena izmed njih je bila, da bi se vse objekte shranjevalo v neko bazo podatkov, ki bi omogočala
preslikavo bazičnih podatkov v objekte, kar bi z vidika robustnosti bila zelo dobra izbira, a bi to zahtevalo veliko prenovo
vseh sektorjev, zato se je na koncu izbrala preprosta opcija shranjevanja objektov, ki preko :mod:`pickle` modula shrani vse račune
ob vsakem normalnem izklopu ogrodja ali pa v vsakem primeru na dve minuti periodično. V prihodnosti so
še vedno načrti za izboljšanje tega mehanizma in možnost uporabe prej omenjene podatkovne bazene ni izključena.

V nadzornem sektorju se poleg programskega vmesnika nahaja tudi HTTP vmesnik, ki služi kot
podpora za oddaljen dostop grafičnega vmesnika do jedra. Deluje na knjižnici `aiohttp <https://docs.aiohttp.org/en/stable/index.html>`_, ki je asinhrona
HTTP knjižnica.
HTTP vmesnik je v resnici zelo preprost in deluje tako, da ob neki HTTP zahtevi ustvari novo :mod:`asyncio` opravilo,
ki potem zahtevo posreduje programskemu vmesniku, kar pomeni, da je rezultat enak tistemu, ki bi ga dobili ob lokalnem delovanju na isti napravi.
Vsi podatki se na HTTP vmesniku pretakajo v JSON formatu.
Osnoven koncept je prikazan na spodnji sliki, kjer je z barvo puščic prikazan ločen potek.


.. _gui-core-connection:
.. figure:: ./DEP/daf-core-http-api.drawio.svg

    Povezava do jedra

.. raw:: latex

    \newpage

Sektor uporabniških računov
-----------------------------
Sektor uporabniških računov je zadolžen za upravljanje z uporabniškimi računi.
Za dodajanje novega uporabniškega računa morajo uporabniki ustvariti :class:`daf.client.ACCOUNT` [#external_obj_ref]_ objekt.
V primeru, da je bil podan uporabniški žeton (angl. *token*), sektor takoj ustvari povezavo na sektor ovoja Discord API, če sta bila podana
uporabniško ime in geslo, pa sektorju brskalnika poda zahtevo za prijavo preko brskalnika, iz katerega potem pridobi
uporabniški žeton in zatem ustvari povezavo na sektor ovoja Discord API.

.. [#external_obj_ref]
    Vsebina včasih vsebuje reference na objekte, ki niso podrobno opisani v diplomskem delu, 
    so pa na voljo v uradni spletni dokumentaciji projekta: https://daf.davidhozic.com/en/v2.9.x/


.. figure:: ./DEP/daf-account-layer-flowchart.svg

    Delovanje sektorja uporabiških računov

.. raw:: latex

    \newpage

Cehovski sektor
---------------
Cehovski sektor je primarno zadolžen za upravljanje s cehi (strežniki).

Sektorju pripadajo trije razredi:

- |GUILD|,
- |USER|,
- |AutoGUILD|.

|GUILD| in |USER| sta med seboj praktično enaka, edina razlika med njima je ta,
da |USER| predstavlja osebe, katerim bomo pošiljali sporočila, |GUILD| pa predstavlja
cehe s kanali.

|AutoGUILD| pa po drugi strani sam po sebi ne predstavlja točno specifičnega ceha, ampak več cehov, katerih ime
se ujema s podanim RegEx vzorcem.

Sam cehovski sektor na začetku razvoja sploh ni bil potreben, a je bil vseeno dodan, preprosto zaradi boljše preglednosti
ne samo notranje kode, ampak tudi kode za definiranje same oglaševalske skripte ob velikem številu sporočil.
To je sicer posledično zahtevalo definicijo dodatnih vrstic v oglaševalski skripti, kar je hitro postalo opazno ob 90 različnih cehih.
Vseeno se je ta izbira dobro izšla, saj je zdaj na cehovskem sektorju veliko funkcionalnosti, ki ne spadajo v ostale sektorje, 
kot je na primer avtomatično iskanje novih cehov in njihovo pridruževanje. Ta struktura nudi tudi veliko preglednosti
v primeru beleženja sporočil (vsaj v primeru JSON datotek), kjer je vse razdeljeno po različnih cehih.


.. figure:: ./DEP/daf-guild-layer-flowchart.svg

    Delovanje cehovskega sektorja

.. raw:: latex

    \newpage

Sporočilni sektor
-----------------
Sporočilni sektor je zadolžen za pošiljanje dejanskih sporočil v posamezne kanale.
V tem sektorju so na voljo trije glavni razredi za ustvarjanje različnih vrst sporočil:

1. |TextMESSAGE| - pošiljanje tekstovnih sporočil v cehovske kanale,
2. |VoiceMESSAGE| - predvajanje zvočnih posnetkov v cehovskih kanalih,
3. |DirectMESSAGE| - pošiljanje tekstovnih sporočil v zasebna sporočila enega samega uporabnika.


|TextMESSAGE| in |DirectMESSAGE| sta si precej podobna, primarno gre v obeh primerih za tekstovna sporočila, razlika
je v kanalih, ki jih |DirectMESSAGE| nima, temveč pošilja sporočila v direktna sporočila uporabnika.
|VoiceMESSAGE| in |TextMESSAGE| sta si po vrsti podatkov sicer različna, vendar pa oba pošiljata sporočila v kanale, ki
pripadajo nekemu cehu, in imata praktično enako inicializacijo.

Pripravljenost sporočila za pošiljanje določa notranji atribut objekta, ki predstavlja točno specifičen čas naslednjega
pošiljanja sporočila. V primeru, da je trenutni čas večji od tega atributa, je sporočilo pripravljeno za pošiljanje.
Ob ponastavitvi "časovnika" se ta atribut prišteje za konfigurirano periodo.
Torej čas pošiljanja ni relativen na dejanski prejšnji čas pošiljanja, temveč je relativen na predvideni prejšnji čas pošiljanja.
Taka vrsta računanja časa omogoča določeno toleranco pri pošiljanju sporočila, saj se zaradi raznih zakasnitev in omejitev
zahtev (angl. *Rate limiting*) na Discord API dejansko sporočilo lahko pošlje kasneje kot predvideno.
To je predvsem pomembno v primeru, ko imamo definiranih veliko sporočil v enem računu, kar je zagotovilo, da se sporočilo ne bo
poslalo točno ob določenem času. Ker se čas prišteva od prejšnjega predvidenega časa pošiljanja, bo v primeru
zamude sporočila razmak med tem in naslednjim sporočilom manjši točno za to časovno napako (če privzamemo, da ne bo ponovne zakasnitve).

Pred tem algoritmom je bil za določanje časa pošiljanja v rabi preprost časovnik, ki se je ponastavil po vsakem pošiljanju, a se je zaradi Discordove
omejitve API zahtevkov in tudi drugih Discord API zakasnitev čas pošiljanja vedno pomikal malo naprej, kar je pomenilo, da če je uporabnik
ogrodje konfiguriral, da se neko sporočilo pošlje vsak dan, in definiral čas začetka npr. naslednje jutro ob 10.00 (torej pošiljanje vsak dan ob tej uri),
potem je po (sicer veliko) pošiljanjih namesto ob 10.00 uporabnik opazil, da se sporočilo pošlje ob 10.01, 10.02 itd.
Primer računanja časa in odprave časovne napake je prikazan na spodnji sliki.

.. figure:: ./DEP/daf-message-period.svg

    Čas pošiljanja sporočila z upoštevanjem časa procesiranja


.. figure:: ./DEP/daf-message-process.svg

    Delovanje sporočilnega sektorja

.. raw:: latex

    \newpage

Sektor beleženja zgodovine sporočil
------------------------------------
Sektor beleženja je zadolžen za beleženje poslanih sporočil oz. beleženje poskusov pošiljanja sporočil. Podatke, ki jih
mora zabeležiti, dobi iz cehovskega sektorja. Beleži se tudi podatke o pridružitvi novih članov, če
je to konfigurirano v cehovskem sektorju.

Omogoča beleženje v tri različne formate, kjer vsakemu pripada lasten objekt beleženja:

1. JSON - :class:`~daf.logging.LoggerJSON`
2. CSV (nekatera polja so JSON) - :class:`~daf.logging.LoggerCSV`
3. SQL - :class:`~daf.logging.sql.LoggerSQL`


Ob inicializaciji jedra se v nadzornem sektorju poda želen objekt beleženja, ki se inicializira in shrani v sektor beleženja.
Po svoji lastni inicializaciji se inicializira še njegov nadomestni (``fallback`` parameter)
objekt, ki se uporabi v primeru kakršnekoli napake pri beleženju.

Po vsakem poslanem sporočilu se iz cehovskega sektorja naredi zahteva, ki vsebuje podatke o cehu, poslanem sporočilu oz.
poskusu pošiljanja ter podatke o uporabniškem računu, ki je sporočilo poslal. Sektor beleženja posreduje zahtevo
izbranemu objektu beleženja, ki v primeru napake dvigne Python napako (angl. *exception*), na kar sektor beleženja 
reagira tako, da začasno zamenja objekt beleženja na njegov nadomestek in ponovno poskusi. Poskuša, dokler mu ne
zmanjka nadomestkov ali pa je beleženje uspešno.

Pred JSON, CSV in SQL beleženjem se je vse beležilo v Markdown datoteke, kjer se je lahko podatke pregledovalo v berljivem formatu,
vendar je bila ta vrsta beleženja kasneje zamenjana z JSON beleženjem.


.. figure:: ./DEP/daf-high-level-log.svg

    Višji nivo beleženja



JSON beleženje
~~~~~~~~~~~~~~~~~
Kot že prej omenjeno, je JSON beleženje zamenjava za Markdown format beleženja. Razlog za zamenjavo je morebitna
implementacija analitike, kar bi se v Markdown formatu težko implementiralo. V času pisanja je analitika na voljo le v
primeru SQL beleženja.

JSON beleženje je implementirano z objektom beleženja :class:`~daf.logging.LoggerJSON`.
Ta vrsta beleženja nima nobene specifične inicializacije, kliče se le inicializacijska metoda njegovega morebitnega
nadomestka.

Ob zahtevi beleženja objekt :class:`~daf.logging.LoggerJSON` najprej pogleda trenuten datum, iz katerega tvori
končno pot do datoteke od (v parametrih) konfigurirane osnovne poti. Končna pot je določena kot ``Leto/Mesec/Dan/<Ime Ceha>.json``.

To pot, v primeru, da ne obstaja, ustvari in zatem z uporabo vgrajenega Python modula :mod:`json` podatke shrani v
datoteko.


.. figure:: ./DEP/daf-logging-json.svg

    Process JSON beleženja



CSV beleženje
~~~~~~~~~~~~~~~~~~
CSV beleženje deluje na enak način kot JSON beleženje. Edina razlika je v formatu, v tem primeru je to CSV.
Lokacija datotek je enaka kot pri JSON beleženju. Za shranjevanje je uporabljen vgrajen Python modul :mod:`csv`.

Za sam pregled poslanih sporočil to ni najbolj primeren format, saj se vse shrani v eni datoteki, pri čemer za razliko od JSON
formata ni večslojnih struktur.


.. raw:: latex

    \newpage


SQL beleženje
~~~~~~~~~~~~~~~~~~
SQL beleženje deluje precej drugače kot delujeta JSON beleženje in CSV beleženje, saj se podatki shranjujejo
v podatkovno bazo, ki je v primeru uporabe SQLite dialekta lahko tudi datoteka.

Beleženje je omogočeno v štirih SQL dialektih:

1. SQLite,
2. Microsoft SQL Server (T-SQL),
3. PostgreSQL,
4. MySQL/MariaDB.

Za čim bolj univerzalno implementacijo na vseh dialektih je bila pri razvoju uporabljena knjižnica :mod:`SQLAlchemy`.

Celoten sistem SQL beleženja je implementiran s pomočjo ORM, kar med drugim omogoča,
da SQL tabele predstavimo s Python razredi, posamezne vnose v bazo podatkov oz. vrstice pa predstavimo z instancami
teh razredov. Z ORM lahko skoraj v celoti skrijemo SQL in delamo neposredno s Python objekti, ki so lahko tudi gnezdene
strukture, npr. vnos dveh ločenih tabel lahko predstavimo z dvema ločenima instancama, kjer je ena instanca 
gnezdena znotraj druge.

Ta vrsta beleženja je bila pravzaprav narejena v okviru zaključnega projekta pri predmetu Informacijski sistemi v 2. letniku.
Ker smo morali pri predmetu izpolnjevati določene zahteve, je bilo veliko stvari pisanih neposredno v SQL jeziku, a vseeno je bila že takrat
uporabljena knjižnica SQLAlchemy. Zaradi določenih SQL zahtev (funkcije, procedure, prožilci ipd.)
je bila ta vrsta beleženja možna le ob uporabi Microsoft SQL Server dialekta.
Kasneje se je postopoma celotno SQL kodo zamenjalo z ekvivalentno Python kodo, ki preko SQLAlchemy knjižnice dinamično
generira potrebne SQL stavke, zaradi česar so bile odstranjene določene uporabne originalne funkcionalnosti, implementirane
na sektorju same SQL baze, kot so npr. prožilci (angl. *trigger*), ki si jih lahko predstavljamo kot neke odzivne funkcije na dogodke.
Je pa zaradi tega možno uporabljati bazo na več dialektih, dodatno pa je bilo veliko stvari lažje implementirati, saj se ni bilo
potrebno zanašati na specifike dialekta.


.. figure:: ./DEP/sql_er.drawio.svg

    SQL entitetno-relacijski diagram [#sql_er_diag]_



.. [#sql_er_diag] Relacije (tabele) so opisane v uradni dokumentaciji: :ref:`SQL Tables`.

.. raw:: latex

    \newpage

Sektor brskalnika
-------------------------------
Velika večina ogrodja deluje na podlagi ovojnega API sektorja, kjer ta direktno komunicira z Discord API.
Določenih stvari pa se neposredno z Discord API ne da narediti ali pa za izvedbo neke operacije (prepovedane v pogojih uporabe Discorda)
obstaja velika možnost, da Discord suspendira uporabnikov račun.

Za ta namen je bil ustvarjen sektor brskalnika, kjer ogrodje namesto z Discord API komunicira z brskalnikom
Google Chrome. To opravlja s knjižnico `Selenium <https://www.selenium.dev/documentation/webdriver/>`_, ki je namenjena avtomatizaciji brskalnikov
in se posledično uporablja tudi kot orodje za avtomatično testiranje spletnih grafičnih vmesnikov.

V ogrodju Selenium ni uporabljen za testiranje, temveč za avtomatično prijavljanje v Discord z uporabniškim
imenom in geslom ter za pridruževanje novim cehom. Dejansko ta sektor posnema živega uporabnika.

.. figure:: ./DEP/daf-selenium-layer.svg

    Delovanje sektorja brskalnika

.. raw:: latex

    \newpage

Ovojni Discord API sektor
-----------------------------
Sektor, ki ovija Discord API, ni striktno del samega ogrodja, ampak je to knjižnica oz. ogrodje `Pycord <https://docs.pycord.dev/en/stable/>`_.
PyCord je odprtokodno ogrodje, ki je nastalo iz kode starejšega `discord.py <https://discordpy.readthedocs.io/en/stable/>`_.
Ogrodje PyCord skoraj popolnoma zakrije Discord API z raznimi objekti, ki jih ogrodje interno uporablja.

Če bi si ogledali izvorno kodo (angl. *source code*) ogrodja, bi opazili, da je poleg ``daf`` paketa tudi paket z imenom ``_discord``.
To ni nič drugega kot PyCord ogrodje, le da je modificirano za možnost rabe na uporabniških računih (poleg avtomatiziranih robotskih računov).

