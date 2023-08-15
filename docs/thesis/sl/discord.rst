===================
Discord
===================

.. _`Developer mode`: https://support.discord.com/hc/en-us/articles/206346498-Where-can-I-find-my-User-Server-Message-ID-

.. _`API Reference`: https://discord.com/developers/docs/topics/opcodes-and-status-codes


Kaj je Discord
==================
Discord je bil ustvarjen leta 2015 s strani Discord Inc. (prej znan kot Hammer & Chisel), studia za razvoj iger, ki sta ga ustanovila Jason Citron in Stanislav Vishnevskiy.
Platforma je bila zasnovana kot orodje za komunikacijo med igralci video iger. :ref:`discord_company`

Zamisel za Discord je izvirala iz Citronove osebne izkušnje v vlogi igralca računalniških igric.
Opazil je, da so mnoga obstoječa orodja za komunikacijo (Skype, TeamSpeak) za igralce zastarela in težko uporabna,
zato je želel ustvariti uporabniku bolj prijazno platformo, ki bi igralcem omogočila enostavno komuniciranje med igranjem iger.

Discord se je od takrat razvil v več kot samo orodje za komunikacijo med igralci video iger in postal priljubljena platforma za skupnosti vseh vrst.
Je priljubljena platforma, ki uporabnikom omogoča komunikacijo preko glasovnega, video in besedilnega klepeta.
Pogosto se uporablja za različne namene, vključno z razpravljanjem o umetniških projektih, načrtovanjem družinskih izletov, iskanjem pomoči pri domačih nalogah.
Prav tako ima dobro funkcijo iskanja nekoč objavljene vsebine, ki je uporabna na primer za iskanje primera dispozicije diplomske naloge, ki jo je nekdo objavil pred tremi meseci.

Čeprav lahko Discord skupnostim vseh velikosti služi kot dom, je še posebej priljubljen med manjšimi aktivnimi skupinami, ki med seboj pogosto komunicirajo.
Večina skupnosti (strežnikov/cehov) je zasebnih in zahtevajo povabilo za vstop, kar  prijateljem in skupnostim omogoča, da ostanejo povezani.
Vendar pa obstajajo tudi večje, bolj javne skupnosti, osredotočene na določene teme, kot so priljubljene videoigre,
ali pa, kot je to v primeru tega diplomskega dela, stvari, kot sta veriga blokov (angl. *blockchain*) in NFT.
Uporablja se lahko tudi kot skupnost fakultete, kjer študenti lahko govorijo preko glasovnih kanalov, delijo študijske materiale
in postavljajo vprašanja o gradivu, ki ga ne razumejo.

Nekaj primerov Discord skupnosti, povezanih z Univerzo v Ljubljani:

- Študentski svet FE (:numref:`ssfe-community-fig`),
- FE UNI,
- FE VSŠ,
- FRI UNI
- in druge.


.. _ssfe-community-fig:
.. figure:: ./DEP/ssfe_discord.png

    ŠSFE Discord skupnost (strežnik oz. ceh)


.. raw:: latex

    \newpage


Struktura omrežja Discord
==========================

Discord aplikacija je v osnovi sestavljena iz gumba za direktna (osebna) sporočila, seznama cehov/strežnikov, seznama kanalov
in seznama uporabnikov (uporabniških računov), ki so pridruženi v ceh. :ref:`discord_interface`.

.. figure:: ./DEP/discord_client_struct.drawio.png

    Struktura Discord aplikacije



Uporabniški računi
----------------------
Obstajata dve vrsti računov, ki sta lahko v cehu:

1. Uporabniški računi
2. Robotski (avtomatizirani) računi

Discordovi pogoji uporabe prepovedujejo avtomatiziranje uporabniških računov [#selfbots]_.

.. [#selfbots] "Automated user accounts (self-bots)": https://support.discord.com/hc/en-us/articles/115002192352-Automated-user-accounts-self-bots-.


Kanali
---------------
Discord ima tri vrste kanalov:

1. Tekstovni kanali - kanali za pisanje besedila v cehu
2. Glasovni kanali - kanali za govor in predvajanje glasbe
3. Direktna sporočila - kanali za pogovor (tekstovno ali glasovno) med dvema uporabnikoma

Tekstovni kanali se nahajajo v cehih in se jih lahko prepozna glede na simbol *#*, ki se nahaja pred imenom vsakega
kanala. Sem lahko uporabnik pošilja navaden tekst, emotikone, binarne datoteke, nalepke ter v primeru robotskega (angl. *bot*) računa
tudi tako imenovana vgrajena sporočila (angl. *Embedded messages* oz. *Embeds*), ki so malo bolj formatirana sporočila
znotraj okrašene škatle (:numref:`discord-embedded-message`).


.. figure:: ./DEP/discord_text_channel.png

    Discordov tekstovni kanal


.. _discord-embedded-message:
.. figure:: ./DEP/discord-embedded-message.png

    Vgrajeno sporočilo


Tako kot se tekstovni kanali lahko uporabljajo za pošiljanje tekstovnih sporočil, se analogno lahko v glasovne kanale
pošilja glasovna sporočila oz. se lahko v njih pogovarja preko mikrofona ali pa predvaja glasbo.
Za samo oglaševanje ti kanali niso tako aktualni, saj bi oglase lahko prejeli le uporabniki, ki so v času
oglaševanja prisotni v kanalu.


.. figure:: ./DEP/discord_voice_channel.png

    Discordov glasovni kanal


Direktna oz. osebna sporočila so namenjena komunikaciji ena na ena med dvema uporabnikoma.
Pošiljanje oglasov v ta sporočila bi sicer prineslo velik doseg uporabnikov, vendar je oglaševanje v direktna sporočila na
vsiljiv oz. agresiven način v Discordovih pogojih uporabe prepovedano, kar pomeni, da lahko v tem primeru Discord ukine uporabnikov račun.

.. figure:: ./DEP/discord_direct_message_channel.png

    Discordova direktna sporočila



Oglaševanje po omrežju Discord 
===============================
Po Discord omrežju se lahko oglašuje širok nabor tem, med katerimi so
video igre, kreativni projekti, produkti, usluge ipd. Ne sme pa se oglaševati nelegalnih vsebin oz. vsebin,
ki spodbujajo kršenje zakona, in vsebin, ki bi lahko povzročile škodo posameznikom :ref:`discord_guidelines`.

Oglašuje se lahko ročno ali pa avtomatično s primernim orodjem.
Oglaševanje vključuje pisanje vsebine oglasa, ustvarjanje uporabniških računov, iskanje cehov, kamor se z uporabniškimi računi pridruži,
in večkratno periodično pošiljanje sporočil v kanale cehov. Najpogosteje se za oglaševanje uporabljajo tekstovni kanali.


Generiranje vsebine
---------------------------
Oglaševalsko vsebino se lahko napiše na pamet iz glave ali pa se za to uporabi orodja, kot je na primer
GPT :ref:`gpt3_content_generation`.

GPT-3 je najsodobnejši jezikovni model umetne inteligence, ki ga je razvilo podjetje OpenAI.
Ima sposobnost generiranja besedila, ki se zdi človeško, in opravljanja različnih nalog, kot so prevajanje, povzemanje in odgovarjanje na vprašanja.
GPT-3 je največji in najmočnejši jezikovni model do danes, s kapaciteto 175 milijard parametrov.
Prislužil si je pozornost tako raziskovalcev kot industrijskih strokovnjakov zaradi svojih impresivnih sposobnosti in potencialnih aplikacij.

Za referenco, prejšnji odstavek je generiral GPT-3 sam.


Za generacijo oglaševalske vsebine lahko npr. GPT-ju podamo naslednjo zahtevo:

*"Write advertisement for my White Rabbit NFT project which came out in 2023. 
We have over 9000 different NFT available for purchase. Talk about the limited Gray Rabbit NFT (only 50 available). Get additional information here www.mynft.domain"*

In njegov rezultat bo:

*"Attention all NFT collectors and art enthusiasts!
We are excited to announce the launch of our White Rabbit NFT project, featuring over 9000 unique and one-of-a-kind digital art pieces. But that's not all - we have a special edition of limited Gray Rabbit NFTs available for purchase, with only 50 available worldwide.
Don't miss out on the opportunity to own a piece of digital art history. These Gray Rabbit NFTs are sure to become highly sought after and increase in value over time.
But act fast - there are only 50 available, and once they're gone, they're gone for good.
For more information and to purchase your own Gray Rabbit NFT, visit www.mynft.domain. Don't wait - add one of these rare and valuable NFTs to your collection today!"*





Iskanje cehov za oglaševanje
------------------------------
Ko je oglaševalska vsebina napisana, je potrebno najti cehe, kamor se bo to vsebino pošiljalo.
Dober kraj za začetek je kar nek spletni iskalnik.
Nabor cehov ponuja tudi Discord sam, ampak za to, da nek ceh pride na ta seznam, mora imeti zagotovljenih kar
nekaj pogojev, med katerimi je tudi ta, da mora imeti vsaj 1000 članov. To je primerno, če želimo oglaševati v večje cehe,
v primeru manjših cehov pa moramo te najti drugje.

Na srečo obstajajo tudi druge strani za iskanje cehov, kot je na primer spletna stran `Top.GG <https://top.gg>`_.
Na tej strani lahko v vgrajen iskalnik dodamo določene parametre, med katerimi je tudi imenska poizvedba, kjer lahko
uporabimo akronim "NFT" in spletna stran nam bo vrnila cehe, povezane z NFT.

Tem cehom se lahko potem pridružimo in našo vsebino oglašujemo v primerne kanale. Cehi na temo NFT in kripto valut
imajo ponavadi namenske kanale, ki so namenjeni oglaševanju, in lahko vanje oglašujemo brez posledic, medtem ko nas
oglaševanje v drugih kanalih lahko privede do izključitve s strežnika.

.. figure:: ./DEP/topgg_find_servers.png
    :width: 15cm
    :align: center

    Iskanje cehov na Top.GG :ref:`top_gg_site`


.. raw:: latex

    \blankpage
