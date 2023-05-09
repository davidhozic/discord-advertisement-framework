=============================
Testiranje projekta
=============================

.. _PyTest: https://docs.pytest.org/

Za zagotavljanje, da ob novih verzijah projekta ne pride do napak, ko spreminjamo funkcionalnost, je za preverjanje delovanja
implementirano avtomatično testiranje (*Unit testing*).

Vsi avtomatični testi so pisani znotraj ogrodja za testiranje z imenom Pytest_.


PyTest - ogrodje za testiranje
=================================

Like the name suggests, PyTest is a powerful, feature-rich testing framework for Python.
It is used to write and run tests for software projects,
and is considered to be one of the best testing frameworks available for Python.

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

.. literalinclude:: ./DEP/test_period_dynamic.py
    :caption: Testi za testiranje periode
    :language: python
