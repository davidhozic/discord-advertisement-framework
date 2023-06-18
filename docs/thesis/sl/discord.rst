===================
Discord
===================

.. _`Developer mode`: https://support.discord.com/hc/en-us/articles/206346498-Where-can-I-find-my-User-Server-Message-ID-

.. _`API Reference`: https://discord.com/developers/docs/topics/opcodes-and-status-codes

Projekt se fokusira na oglaševanje po Discordu-u in za to da bi bil preostanek diplomskega dela bolj razumljiv, to poglavje
vsebuje nekaj informacij o Discord-u - Osnovne informacije, kako je nastal in kako deluje.

Kaj je Discord
==================
Discord je bil ustvarjen leta 2015 s strani Discord Inc (prej znan kot Hammer & Chisel), studia za razvoj iger, ki sta ga ustanovila Jason Citron in Stanislav Vishnevskiy.
Platforma je bila zasnovana kot orodje za komunikacijo med igralci video iger.

Zamisel za Discord je izvirala iz Citronove osebne izkušnje v vlogi igralca računalniških igric.
Opazil je, da so mnoga obstoječa orodja za komunikacijo (Skype, TeamSpeak) za igralce zastarela in težko uporabna,
in želel je ustvariti bolj uporabniku prijazno platformo, ki bi igralcem omogočila enostavno komuniciranje med seboj med igranjem iger.

Discord se je od takrat razvil v več kot samo orodje za komunikacijo med igralci video iger in postal
priljubljena platforma za skupnosti vseh vrst, da se povežejo in komunicirajo.
Uporabljajo ga milijoni po vsem svetu za vse od igranja iger do izobraževanja in druženja.

Discord je priljubljena komunikacijska platforma, ki uporabnikom omogoča komuniciranje preko glasovnega, video in besedilnega klepeta.
Discord se pogosto uporablja za različne namene, vključno z razpravljanjem o umetniških projektih, načrtovanjem družinskih izletov, iskanjem pomoči pri domačih nalogah.
Prav tako ima dobro funkcijo iskanja za iskanje vsebine, ki je bila nekoč objavljena, kar je koristno, na primer, pri iskanju roka izpita, ki ga je nekdo objavil pred mesecem dni.

Čeprav lahko Discord služi kot dom skupnostim vseh velikosti, je še posebej priljubljen med manjšimi, aktivnimi skupinami, ki med seboj pogosto komunicirajo.
Večina strežnikov Discord je zasebnih in zahtevajo povabilo za vstop, kar omogoča prijateljem in skupnostim, da ostanejo povezani.
Vendar pa obstajajo tudi večje, bolj javne skupnosti, osredotočene na določene teme, kot so priljubljene videoigre
ali pa, v primeru te naloge, stvari kot so blockchain in NFT.
Uporablja se lahko tudi kot skupnost fakultete / šole, kjer študenti lahko govorijo preko glasovnih kanalov, delijo študijske materiale
in postavljajo vprašanja o gradivu, ki ga ne razumejo.
Nekaj primerov skupnosti Discord, povezanih s Univerzo v Ljubljani:

- :ref:`Student council of Faculty of Electrical Engineering (ŠSFE) <ssfe-community-fig>`,
- :ref:`FE UNI <fe-uni-community-fig>` ,
- FE VSŠ,
- FRI UNI,
- ...


.. figure:: ./DEP/discord_logo.svg
    :width: 400

    Discord brand


.. _ssfe-community-fig:
.. figure:: ./DEP/ssfe_discord.png
    :width: 400

    ŠSFE Discord community


.. _fe-uni-community-fig:
.. figure:: ./DEP/feuni_discord.png
    :width: 400

    FE UNI Discord community


.. raw:: latex

    \newpage


Discordova struktura
======================

.. figure:: ./DEP/discord_client_struct.drawio.png

    Struktura aplikacije

Discord klient je aplikacija, prek katere lahko uporabniki komunicirajo.
V jedru je sestavljena iz gumba za direktna (osebna) sporočila, seznama cehov, seznama kanalov in seznama uporabnikov,
ki so pridruženi v ceh.
Obstajata dve vrsti računov, ki sta lahko v cehu:

1. Uporabniški računi
2. Avtomatizirani (robotski) računi

Discordovi pogoji uporabe prepovedujejo avtomatiziranje uporabniških računov.


Vloge
--------------
Discord ima pravice narejene po principu vlog, kjer vsaka vloga določa katere pravice bo posamezen uporabnik imel v
cehu in kanalu. Uporabne so npr. za skrivanje šolskih kanalov tretjih letnikov v primeru da je nek uporavnik drugi letnik.


Kanali
---------------
Discord ima tri vrste kanalov:

1. Tekstovni kanali - kanali za pisanje besedila v cehu,
2. Glasovni kanali - kanali za govor in predvajanje glasbe
3. Direktna sporočila - Kanali za pogovor (tekstovno ali glasovno) z enim samim uporabnikom.

Tekstovni kanali se nahajo v cehih in se jih lahko prepozna glede na simbol *#*, ki se nahaja pred imenom vsakega
kanala. Sem lahko pošiljate navaden tekst, emotikone, nalepke in darila ter, v primeru da imate avtomatiziran račun,
lahko pošiljate tudi tako imenovana vgrajena sporočila (*Embedded messages*), ki so malo bolj formatirana sporočila
znotraj nekakšne škatle - pogosto se jih uporablja za oglase.

.. figure:: ./DEP/discord_text_channel.png

    Discord tekstovni kanal

Tako kot se tekstovni kanali lahko uporabljajo za pošiljanje tekstovnih sporočil, se analogno lahko v glasovne kanale
lahko pošilja glasovna sporočila oz. se lahko v njih pogovarja preko mikrofona ali pa predvaja glasbo.
Za samo oglaševanja te kanali niso tako aktualni, saj bi vaše oglase lahko prejeli le uporabniki, ki so v času
oglaševanja v kanalu.


.. figure:: ./DEP/discord_voice_channel.png

    Discord glasovni kanal


Direktna oz. osebna sporočila so za razliko od zgornjih kanalov, namenjena komuniciranju z enim samin uporabnikom.
Sem noter sta všteta tekstovni kanal uporabnika ter tudi glasovna komunikacija. V zvezi z *Shillingom* oz. vsiljivega
oglaševanja so te najbližje vsiljivi kategoriji, vendar je to prepovedano v pogojih uporabe Discord-a in v primeru
prevelikega in hitrega oglaševanja v direktna sporočila, lahko Discord ukine vaš račun.

.. figure:: ./DEP/discord_direct_message_channel.png

    Discord direktna sporočila


.. raw:: latex

    \newpage


Oglaševanje v Discord
==========================
Kot je bilo razloženo v :ref:`Marketinški pristopi za promoviranje nezamenljivih žetonov`, je *shilling* vrsta oglaševanja.
V Discord se lahko oglašuje ročno ali pa avtomatično z primernim orodjem.


Ročno oglaševanje
---------------------
Ročno oglaševanje vključuje pisanje vašega oglasa, ustvarjanje računov, iskanje cehov in večkratno periodično pošiljanje
sporočil v kanale oz. v direktna sporočila posameznih uporabnikov.


Generiranje vsebine
^^^^^^^^^^^^^^^^^^^^^^^^^^
Oglaševalsko vsebino se lahko napiše na pamet iz glave ali pa se uporabi malo bolj sofisticirana orodja, kot je to 
GPT (*Generative pretrained transformers*).

GPT-3 je najsodobnejši jezikovni model umetne inteligence, ki ga je razvilo podjetje OpenAI.
Ima sposobnost generiranja besedila, ki se zdi človeško in opravljanja različnih nalog, kot so prevajanje, povzemanje in odgovarjanje na vprašanja.
GPT-3 je največji in najmočnejši jezikovni model do danes, s kapaciteto 175 milijard parametrov.
Prislužil si je pozornost tako raziskovalcev kot industrijskih strokovnjakov zaradi svojih impresivnih sposobnosti in potencialnih aplikacij.

Za referenco, prejšnji odstavek je zgeneriral GPT-3 sam.


Za generacijo oglaševalske vsebina lahko npr. GPT-ju podamo slednjo zahtevo:

*"Write advertisement for my White Rabbit NFT project which came out in 2023. 
We have over 9000 different NFT available for purchase. Talk about the limited Gray Rabbit NFT (only 50 available). Get additional information here www.mynft.domain"*

in njegov rezultat bo:

*"Attention all NFT collectors and art enthusiasts!
We are excited to announce the launch of our White Rabbit NFT project, featuring over 9000 unique and one-of-a-kind digital art pieces. But that's not all - we have a special edition of limited Gray Rabbit NFTs available for purchase, with only 50 available worldwide.
Don't miss out on the opportunity to own a piece of digital art history. These Gray Rabbit NFTs are sure to become highly sought after and increase in value over time.
But act fast - there are only 50 available, and once they're gone, they're gone for good.
For more information and to purchase your own Gray Rabbit NFT, visit www.mynft.domain. Don't wait - add one of these rare and valuable NFTs to your collection today!"*

Ko imate oglaševalsko vsebino jo samo prepošiljate po vseh kanalih.

.. figure:: ./DEP/chatgpt.png
    :width: 400

    Primer Chat-GPT


Iskanje cehov za oglaševanje
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Ko enkrat imate oglaševalsko vsebino, rabite najti cehe kamor boste to vsebino pošiljali.
Dober kraj za začetek je kar nek spletni iskalnik.
Nabor cehov ponuja tudi kar Discord sam, ampak za to da nek ceh pride na njihov seznam mora imeti zagotovljenih kar
nekaj pogojev med katerimi je tudi ta da mora imeti ceh vsaj 1000 uporabnikov. To posledično pomeni da ima ceh verjetno
politiko proti pretiranem oglaševanju, za to morda ta seznam ni najbolj primeren za to rabo.

Na srečo obstajajo tudi drugi strani za iskanje cehov, kot je na primer spletna stran `Top.GG <https://top.gg>`_.
Na tej strani lahko v vgrajeni iskalnik dodamo določene parametre med katerimi je tudi imenska poizvedba v kateri lahko
uporabimo akronim "NFT" in spletna stran nam bo vrnila cehe povezane z NFT.

Tem cehom se lahko potem pridružimo in v primerne kanale oglašujemo našo vsebino. Cehi na temo NFT in kripto valut
imajo ponavadi namenske kanale, ki so namenjeni oglaševanju in v te lahko oglašujemo brez posledic, medtem ko nas
oglaševanje v drugih kanalih lahko privede do izključitve iz strežnika.

.. figure:: ./DEP/topgg_find_servers.png
    :width: 15cm

    Iskanje cehov na Top.GG

