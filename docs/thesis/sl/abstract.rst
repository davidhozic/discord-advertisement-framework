
.. only:: html

    =============
    Povzetek
    =============

    .. rubric:: Povzetek

.. Prevent inclusion of this "title" into index
.. raw:: latex

    \chapter*{Povzetek}

.. 
    .. sourcelist::

        .. source:: Test title
            :id: id_david
            :author: David Hozic
            :url: https://daf.davidhozic.com
            :last_checked: 01. 2023

        .. source:: Test title
            :id: id_david
            :author: David Hozic
            :url: https://daf.davidhozic.com
            :last_checked: 01. 2023

        .. source:: Test title
            :id: id_david
            :author: David Hozic
            :url: https://daf.davidhozic.com
            :last_checked: 01. 2023




Nezamenljivi žetoni (angl. Non fungible tokens - NFT) so edinstvena digitalna sredstva, ki živijo na verigi blokov brez možnosti replikacije.
Obstaj več pristopov za njihovo oglaševanje, kjer je eden izmed teh oglaševanje po socialnem omrežju Discord s pristopom šilinga.
Diplomsko delo se fokusira na proces oglaševanja in se navezuje na projekt Ogrodje za oglaševanje po Discordu (angl. Discord Advertisement Framework),
ki je implementirano v programskem jeziku Python.

Najprej so v delu opisani nezamenljivi žetoni, oziroma pristopi k njihovem oglaševanju.
Zatem je predstavljeno socialno omrežje Discord in pristop oglaševanja na tem omrežju.
Sledi predstavitev samega projekta diplomske naloge, kjer je cilj naloge izdelava ogrodja za oglaševanje po Discordu,
ki lahko deluje samodejno brez nadzora uporabnika, se ustrezno odziva na napake, nudi beleženje sporočil in je konfigurabilno,
da lahko deluje na več načinov.

V poglavju vezanem na projekt diplomskega dela so predstavljeni zasnova in razvoj projekta, njegova dokumentacija in avtomatično testiranje.

Ogrodje se na najvišjem nivoju deli na jedro in grafični vmesnik, kjer jedro lahko deluje neprekinjeno na strežniku in
je sposobno na daljavo procesirati ukaze iz grafičnega vmesnika. Oglaševalske podatke in parametre se v jedru
nastavi kar preko Python skripte / programa, kjer je potrebno minimalno znanje Python jezika.
Jedro se deli na več abstrakcijsih nivojev za lažji razvoj in nadgrajevanje.
Grafični vmesnik je prav tako implementiran v Pythonu. Opisan je razvoj grafičnega vmesnika,
opisana je njegova struktura in na koncu je opisan oddaljen dostop do jedra ogrodja.
Objekte (račune, sporočila, ipd.) se v grafičnem vmesniku definira preko novega okna, ki se samodejno generira na podlagi
podatkovnih tipov prebranih iz izvorne kode funkcij in razredov v jedru ogrodja. Definirane objekte je mogoče shraniti v JSON datoteko oz.
omogočeno je tudi generiranje Python oglaševalske skripte, ki deluje v jedru ogrodja.

Po opisu razvoja in zasnove jedra ter grafičnega vmesnika ogrodja, je opisan proces dokumentacije.
Dokumentacija je izdelana s sistemom Sphinx, in se avtomatično gradi in objavlja ob vsaki izdaji projekta
preko platforme GitHub. Opis vseh javnih razredov in funkcij (programskega vmesnika) se samodejno generira iz same kode projekta.

Na koncu poglavja o projektu diplomskega dela je opisan še proces avtomatičnega testiranja, kjer je ta implementiran z ogrodjem za
avtomatično testiranje pytest. Ogrodje se, ob vsakem zahtevku za združitev vej na GitHubu, avtomatično testira in zavrne združitev veje, če
katerikoli od testov ne uspe. Z avtomatičnem testiranjem se zmanjšajo možnosti za izdajo nove verzije ogrodja z napakami v delovanju.

Zaključim lahko da je ogrodje izjemno uporabno ne le za oglaševanje NFT, a tudi za oglaševanje katere koli druge vsebine.
Ker v času pisanja ne obstaja skoraj nobeno brezplačno oglaševalsko ogrodje, ki bi bilo sposobno vsega kar je sposobno to ogrodje,
je smiselno sklepati da je projekt izjemno uporabne narave.



**Ključne besede:** Nezamenljivi žetoni, samodejno oglaševanje, šiling, Python, grafični vmesnik, oddaljen dostop,
shranjevanje v datoteko, dokumentacija, avtomatično testiranje, ogrodje za oglaševanje, beleženje sporočil, zasnova in razvoj.


.. only:: html

    .. rubric:: Abstract

.. Prevent inclusion of this "title" into index
.. raw:: latex

    \chapter*{Abstract}

Non-fungible tokens (NFTs) are unique digital assets that exist on a blockchain without the ability of replication.
There are several approaches of advertising them, one of which is advertising on the social network Discord using the shilling approach.
The thesis focuses on the advertisement process and relates to the Discord Advertisement Framework project, implemented in the Python programming language.

First, the thesis describes non-fungible tokens and approaches to their advertisement.
Next, it presents the social network Discord and the advertisement approach on this social network. It also explains the types of user accounts and channel types where advertisement can take place.
The presentation then moves on to the project itself, which aims to create a framework for advertising on Discord,
capable of operating automatically without user supervision, responding appropriately to errors, logging messages, and being configurable to function in multiple ways.

In the chapter related to the thesis's project, the design and development of the project, its documentation and automatic testing are all presented.

At the highest level, the framework is divided into a core and a graphical interface, where the core can run continuously on a server and
is capable of remotely processing commands from the graphical interface. Advertisement data and parameters are set in the core
via a Python script or program, requiring minimal knowledge of the Python language.
The core is divided into several abstraction layers to facilitate development and upgrades.
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

**Keywords:** Non-fungible tokens, automatic advertising, shilling, Python, graphical interface, remote access,
saving to file, documentation, automatic testing, advertisement framework, message logging, design and development.

