========================
Rezultat in zaključek
========================

V okviru diplomskega dela "Ogrodje za oglaševanje nezamenljivih žetonov po socialnem omrežju Discord",
je bil cilj izdelati ogrodje, ki bi lahko neodvisno oglaševalo v več cehih in pošiljalo različna sporočila, vse na enem samem računu.
V planu ni bilo nobene večje razširitve kot oglaševanje NFT, vendar vseeno ogrodje
v končni fazi omogoča univerzalno oglaševanje tako NFT kot katerekoli druge vsebine in ne samo periodično, omogoča
tudi oglaševanje enkratne vsebine. Poleg vsebine je mogoče definirati tudi začeten čas pošiljanja, število pošiljanj in 
periodo pošiljanja. Ogrodje omogoča tudi pošiljanje na več računih hkrati, namesto na enem računu, kot je to bilo na začetku predvideno.
Odporno je na napake pošiljanja, kot so izbrisani kanali, cehi, pomanjkanje pravic, in se nanje ustrezno odziva, kjer
uporabniku preko opozorilnih izpisov omogoča spremljanje delovanja.
Za sledenje zgodovine pošiljanj je podprto beleženje poskusov pošiljanj v več formatih, kjer je eden izmed teh tudi SQL
beleženje, kar omogoča analitiko oziroma statistiko poslanih sporočil in tudi
sledenje pridružnih povezav (angl. *invite link*) za posamezen ceh in s tem spremljanje dosega uporabnikov z določenimi sporočili.
Za iskanje novih cehov je na podlagi brskalnika Google Chrome implementirano iskanje in pridruževanje se novim cehom, kjer
se za iskanje lahko nastavi poljubne parametre in s tem konfigurira, točno katerim cehom se bo ogrodje pridružilo.
Vse zgoraj omenjeno je omogočeno v jedru ogrodja preko Python skripte oziroma konzole, je pa na vrhu izdelan grafičen vmesnik (:numref:`fig-gui-front`) za lažje upravljanje
z ogrodjem, definicijo objektov (računov, cehov, sporočil ipd.) ter prikaz statistike in vsebine poslanih sporočil.
Omogočen je tudi oddaljen dostop do jedra ogrodja, kjer lahko jedro in grafični vmesnik delujeta samostojno in komunicirata
na daljavo preko HTTP vmesnika, kar pomeni, da lahko jedro deluje na nekem oddaljenem strežniku 24/7, grafični vmesnik pa uporabniki
zaženejo ob poljubnem času in se potem povežejo na jedro ogrodja. V :ref:`prilogah <Priloge>` se nahajajo primeri definicij in uporabe.


Z delovanjem ogrodja sem v končni fazi zadovoljen. Zdi se mi, da sem izpolnil vse želene
zahteve, ki jih zahteva samodejno oglaševanje po Discordu, seveda pa se da stvari vedno izboljšati, ne glede na to, kako dobro
so narejene. Discord se tudi kar hitro razvija in dodaja nove funkcionalnosti, ki bi se jih dalo v ogrodju še dodatno podpreti (npr. obvestilni kanali).
Pri pridruževanju v nove cehe se včasih pojavi CAPTCHA test, ki ga mora rešiti uporabnik sam, in ena izmed izboljšav tu bi bila
lahko samodejno reševanje CAPTCHA testov. Prav tako bi se lahko ob vzponu orodij, kot je ChatGPT, izdelalo
samodejno odgovarjanje na vprašanja v direktnih/privatnih sporočilih, ki bi jih drugi uporabniki poslali uporabniku, na katerem deluje ogrodje.

Zaključim lahko, da je projekt izjemno uporaben za oglaševanje po Discordu, saj je zaradi Discordove strukture na platformi
prisotno ogromno povezanih cehov, kamor lahko oglašujemo in s tem orodjem to lahko počnemo avtomatično in preprosto.
Prav tako v času začetka izdelave ogrodja in tudi ob času pisanja tega diplomskega dela ni na vidiku nobenega bolj razširjenega in za uporabo
preprostega ogrodja (vsaj ne brezplačnega), kar daje ogrodju še dodatno vrednost.
