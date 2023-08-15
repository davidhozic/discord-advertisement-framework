
.. only:: not latex

    =============
    Povzetek
    =============

    .. rubric:: Povzetek

.. raw:: latex

    \chapter*{Povzetek}


Nezamenljivi žetoni (angl. *Non-fungible tokens*) so edinstvena digitalna sredstva, 
ki obstajajo na verigi blokov brez možnosti replikacije.
Obstaja več pristopov za njihovo oglaševanje, pri čemer je eden izmed njih oglaševanje preko socialnega omrežja Discord
z agresivnim pristopom.
Diplomsko delo se osredotoča na proces oglaševanja in se nanaša na projekt Ogrodje za oglaševanje preko Discord omrežja
(angl. *Discord Advertisement Framework*), ki je implementirano v programskem jeziku Python.

Najprej so v delu opisani nezamenljivi žetoni in pristopi k njihovemu oglaševanju.
Nato je predstavljeno socialno omrežje Discord in pristop k oglaševanju na njem.
Sledi predstavitev samega projekta diplomskega dela, katerega cilj je izdelava ogrodja za oglaševanje preko Discord omrežja,
ki lahko deluje samodejno, brez posredovanja uporabnika, se ustrezno odziva na napake, nudi beleženje sporočil in je
nastavljivo za različne načine delovanja.

V poglavju, ki se nanaša na projekt diplomskega dela, so predstavljeni zasnova in razvoj projekta,
njegova dokumentacija ter avtomatizirano testiranje.
Ogrodje se na najvišji ravni deli na jedro in grafični vmesnik, pri čemer lahko jedro deluje neprekinjeno na strežniku
in je sposobno procesirati ukaze iz grafičnega vmesnika na daljavo.
Oglaševalske podatke in parametre se v jedru nastavi preko Python datoteke, kar zahteva
minimalno znanje Python jezika. Jedro je razdeljeno na več sektorjev za lažji razvoj in nadgradnjo.
Grafični vmesnik je prav tako implementiran v jeziku Python.
Opisan je razvoj grafičnega vmesnika, predstavljena je njegova struktura, na koncu pa je opisan tudi oddaljen dostop
do jedra ogrodja. Objekte (račune, sporočila ipd.) je mogoče v grafičnem vmesniku definirati preko novega okna,
ki se samodejno generira na podlagi podatkovnih tipov, prebranih iz izvorne kode funkcij in razredov v jedru ogrodja.
Definirane objekte je mogoče shraniti v JSON datoteko, prav tako je omogočeno generiranje Python oglaševalske skripte, ki deluje v jedru ogrodja.

Po opisu razvoja in zasnove jedra ter grafičnega vmesnika ogrodja je opisan proces dokumentiranja.
Dokumentacija je izdelana s sistemom Sphinx in se avtomatično gradi ter objavlja ob vsaki izdaji projekta
preko platforme GitHub. Opis vseh javnih razredov in funkcij (programskega vmesnika) se samodejno generira iz same kode projekta.

Na koncu poglavja o projektu diplomskega dela je opisano še avtomatizirano testiranje kode, ki je implementirano z
ogrodjem za avtomatizirano testiranje pytest. Ogrodje se na platformi GitHub avtomatično testira ob vsakem zahtevku za
združitev veje, pri čemer se združitev zavrne, če katerikoli od testov ni uspešen. Z avtomatiziranim testiranjem se
zmanjšajo možnosti za izdajo nove verzije ogrodja z napakami v delovanju.

Sklepam, da je ogrodje izjemno uporabno, ne le za oglaševanje NFT-jev, temveč tudi za oglaševanje katerekoli druge vsebine.
Ker v času pisanja ni na voljo skoraj nobenega brezplačnega ogrodja za oglaševanje, ki bi bilo sposobno vsega, česar je sposobno to
ogrodje, je smiselno sklepati, da je projekt izjemno uporabne narave.


**Ključne besede:** Python, grafični vmesnik, oddaljen dostop,
shranjevanje v datoteko, dokumentacija, avtomatično testiranje, beleženje sporočil, zasnova in razvoj.


.. only:: not latex

    .. rubric:: Abstract

.. raw:: latex

    \chapter*{Abstract}


First, the thesis describes non-fungible tokens and approaches to their advertisement.
Next, it presents the social network Discord and the advertisement approach on this social network. It also explains the types of user accounts and channel types where advertisement can take place.
The presentation then moves on to the project itself, which aims to create a framework for advertising on Discord,
capable of operating automatically without user intervention, responding appropriately to errors, logging messages, and being configurable to function in multiple ways.

In the chapter related to the thesis's project, the design and development of the project, its documentation and automatic testing are all presented.

At the highest level, the framework is divided into a core and a graphical interface, where the core can run continuously on a server and
is capable of remotely processing commands from the graphical interface. Advertisement data and parameters are set in the core
via a Python script or program, requiring minimal knowledge of the Python language.
The core is divided into several sectors to facilitate development and upgrades.
The graphical interface is also implemented in Python. The development of the graphical interface is described,
its structure is explained, and remote access to the core of the framework is discussed.
Objects (accounts, messages, etc.) are defined in the graphical interface through a new window, automatically generated based on
data types extracted from the source code of functions and classes in the core of the framework. The defined objects can be saved into a JSON file, and
Python advertisement scripts that runs in the core of the framework can also be generated.

After describing the development and design of framework's core and graphical interface, the documentation process is explained.
The documentation is created using the Sphinx system and is automatically built and published with each project release
through the GitHub platform. The description of all public classes and functions (the program's interface) is automatically generated from the project's source code.

Finally, the chapter on the thesis's project describes the process of automated testing (unit testing), which is implemented using the pytest testing framework.
Upon a pull request on the GitHub platform, the framework is automatically tested, and the branch merge is rejected if any of the tests fail.
Automated testing reduces the chances of a new version release being published with bugs being present.

In conclusion, the framework proves to be extremely useful not only for advertising NFTs but also for advertising any other content.
Considering that, at the time of writing, there are almost no free advertising frameworks capable of what this framework can do,
it is reasonable to conclude that the project is of significant practical value.

**Keywords:** Python, graphical interface, remote access,
saving to file, documentation, automatic testing, message logging, design and development.

.. raw:: latex

    \blankpage
