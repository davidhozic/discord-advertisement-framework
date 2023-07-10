====================
Rezultat
====================

Zdaj ko vemo kako je vse zasnovano in razvito, pa povzemimo še skupen rezultat.

V končni fazi je ogrodje je sposobno oglaševati na več računih na enkrat, kjer ima vsak račun lahko več cehov in sporočil.
Cehom se da nastaviti sledenje povezav za pridružitev (angl. *invite links*), vklopiti beleženje sporočil in definicijo le teh.
Cehe se lahko določi z unikatnim *Snowflake* identifikatorjem, kjer to definira točno en ceh ali pa več cehov če uporabimo
funkcionalnost samodejnega odkrivanja cehov na podlagi ReGex vzorcev.

V vsak ceh se lahko pošlje po več sporočil, kjer ima vsako sporočilo svojo periodo pošiljanja, ki je ta lahko fiksna ali pa naključna
znotraj določenega območja. Pošilja se lahko tako tekstovna sporočila kot tudi glasovna, kjer se lahko podatke
definira statično ali pa se sporočilu kot podatek poda funkcijo iz katere se dinamično podatke pridobi vsako periodo (na voljo le brez GUI).
Podobno kot pri cehu se vsak kanal, kamor se bo sporočilo poslano, lahko definira preko *Snowflake* identifikatorja, ki
določa točno določen kanal ali pa preko ReGex vzorca za samodejno najdbo kanalov. Isto sporočilo se da poslati večkrat, kjer
se lahko nastavi po koliko časa se bo sporočilo nehalo pošiljati, lahko pa se nastavi tudi točen čas odstranitve oz.
točno število poslanih sporočil preden se pošiljanje preneha.

Vsako poslano sporočilo se lahko beleži v JSON / CSV datoteko ali pa v bazo podatkov, kjer je še dodatno
na voljo analiza oz. statistika poslanih sporočil, kot tudi statistika koliko ljudi se je pridružilo nekemu cehu.
Rezulatati analize so na voljo preko grafičnega vmesnika ali pa preko metod :class:`~daf.logging.sql.LoggerSQL`, katerih
ime se začne na ``analytic_``.

S pomočjo Google Chrome brskalnika je v ogrodje implementirano samodjeno prijavljanje z uporabniškim imenom in geslom,
kot tudi samodejno iskanje novih cehov (v katere uporabnik še ni pridružen) in napol-samodejno pridruževanje v le te.


Vse zgoraj omenjeno je na voljo v samem jedru ogrodja - kjer ne potrebujemo grafičnega vmesnika, zdaj pa povzemimo še funkcionalnost specifično na grafični vmesnik.

Znotraj grafičnega vmesnika je mogoče definirati shemo vseh računov, upravljalcev beleženja in povezovalnega konektorja na oddaljeno jedro.
Shemo se potem lahko uvozi v delujoče jedro ogrodja, lahko pa se jo kot predlogo shrani v JSON datoteke oz. iz nje izdela
:ref:`ekvivalentno Python skripto <equivalent_script>`, ki deluje popolnoma enako kot bi v grafičnem vmesniku.
Pravzaprav vse kar grafilčni vmesnik naredi iz sheme, ko jo uvozimo v jedro, je da jo pretvori v ustrezno obliki in le to posreduje
jedru, kar posledično pomeni, da grafični vmesnik vedno deluje na enak način kot jedro. Shemo se seveda tudi lahko prebere in uvozi iz JSON datoteke.
Poleg definicije sheme, je možno tudi direkto spremnljanje objektov v ogrodju in modifikacija le teh.

Grafični vmesnik lahko deluje lokalno, kjer jedro ogrodja zažene na isti napravi, lahko pa se poveže na oddaljeno
jedro preko HTTP API vmesnika. Z uporabniškega vidika uporabe ni nobene razlike med lokalnim delovanjem ali pa oddaljenim,
razen te, da se upravljalnik beleženja sporočil lahko definira le ob zagonu ogrodja in ga posledično tudi iz grafičnega vmesnika
na daljavo ni možno spreminjati.

Preko grafičnega vmesnika je možno tabelarno prikazati statistiko poslanih sporočil in prikazati vsebino vsakega preteklega sporočla.
To deluje enako kot v jedru, razlika je le v prikazu podatkov.

To je konec povzetka celotnega rezultata, bolj podrobno uporabo pa je možno razbrati iz uradne :ref:`dokumentacije <Quickstart (GUI)>`.
