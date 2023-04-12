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
    :height: 720

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
cehe z kanali. |AutoGUILD| pa sam po sebi ne predstavlja točno specifičnega ceha, ampak več cehov, katerih ime
se ujema z podanim RegEx vzorcem.


The guild layer is responsible for initializing the message layer and signaling 
the message layer to send messages to channels, whenever it detects a message is ready to be shilled.
It is also responsible for removing any messages that should be deleted, either by design or by critical errors
that require intervention.

The guild layer checks each message if it is to be removed, if not it creates coroutine objects for each message and then awaits
the coroutines which causes the message layer to shill each message to the belonging channels.

After each message send, the guild layer also signals the logging layer to make a log of the just now sent message.

.. error:: **TODO:** Guild layer diagram.


.. raw:: latex

    \newpage


Logging layer
---------------
The logging layer is responsible for saving message logs after getting data from the :ref:`Guild layer`.

Logging is handled thru logging manager objects and it supports 3 different logging schemes:

1. JSON logging - :class:`daf.logging.LoggerJSON`,
2. CSV logging (nested fields are JSON) - :class:`daf.logging.LoggerCSV` and
3. SQL logging (multiple dialects) - :class:`daf.logging.LoggerSQL`


.. figure:: ./DEP/source/guide/core/images/logging_process.drawio.svg
    :width: 300

    Logging layer flow diagram


Upon a logging request from the :ref:`Guild layer`, the logging layer obtains the globally set logging manager and calls
the method responsible for saving the log. If no exceptions are raised the logging layer stays silent.

In case of any exceptions, the logging layers traces the exception to the console, selects the backup (fallback) logging manager that is 
set by the manager's ``fallback`` parameter and repeats the process. It repeats this process until it runs out of fallbacks.

If it runs out of fallbacks, then the log will not be saved and an error will traced to the console notifying the user that
a log will not be saved.
