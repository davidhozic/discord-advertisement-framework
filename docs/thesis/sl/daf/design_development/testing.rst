
=============================
Avtomatično testiranje
=============================

.. _pytest: https://docs.pytest.org/

Za zagotavljanje, da ob novih verzijah projekta ne pride do napak, je za preverjanje delovanja
implementirano avtomatično testiranje.

Vsi avtomatični testi so pisani znotraj ogrodja za testiranje z imenom pytest_.


pytest - ogrodje za testiranje
-------------------------------------
Kot že ime namiguje, je pytest ogrodje za testiranje na Python platformi.

Avtomatične teste se pri pytestu implementira s Python funkcijami, katerih ime se začne s "test".
Testi lahko sprejmejo tudi parametre, kjer so ti lahko tudi pritrditve (angl. *fixture*),
ki jih lahko lahko uporabimo kot inicializacijske funkcije :ref:`pytest_desc`.
V pritrditvi lahko npr. povežemo podatkovno bazo, konektor na bazo vrnemo iz pritrditve, in 
v primeru, da je naš test definiran kot

.. code-block:: python

    
    async def test_example_test(example_fixture):
        ...

bo prejel vrednost, ki jo je pritrditev vrnila. Pritrditev ima lahko različno dolgo življensko dobo/obseg
(npr. globalen obseg, obseg modula, obseg funkcije), kar pomeni, da bo lahko več testov prejelo isto vrednost,
ki jo je pritrditev vrnila, dokler se življenska doba ne izteče.
Pritrditev je lahko tudi Python generator [#py_generator]_, kar nam omogoča inicializacijo testov in
čiščenje na koncu na sledeč način:

.. [#py_generator] https://wiki.python.org/moin/Generators


.. raw:: latex

    \newpage


.. code-block:: python
    :caption: pytest pritrditev z inicializacijo in čiščenjem
    
    @pytest_asyncio.fixture(scope="session")
    def example_fixture(some_other_fixture):
        # Initialization
        database = DataBaseConnector()
        database.connect("discord.svet.fe.uni-lj.si/api/database")

        yield database  # Value that the tests receive

        # Cleanup
        database.disconnect()
        database.cleanup()


Preverjanje, ali je test uspel, se izvede s stavkom ``assert``, ki dvigne :class:`AssertionError` napako, če vrednost v ``assert`` stavku ni enaka ``True``.
V primeru, da je dvignjen AssertionError, pytest zabeleži test kot neuspel in izpiše napako.
Kako podroben bo izpis, se lahko nastavi ob zaganjanju testa, npr.
``pytest -vv``, kjer ``-vv`` nastavi podrobnost. Kot primer si poglejmo, kaj bo izpisal, če v ``assert`` stavek
kot vhod damo primerjavo dveh seznamov.

.. code-block:: python
    :caption: Primerjava dveh seznamov, ki nista enaka

    assert [1, 2, 3] == [1, 2, 3, 4, 5, 6]

Iz zgornjega testa je očitno, da to ne drži in da bo test dvignil napako, ampak v assertu nimamo nobenega
besedila, da bi se izpisalo, kaj je šlo narobe, tako da bi pričakovali, da pytest vrne samo informacijo, da test ni uspel.
Izkaže se, da nam bo pytest izpisal, točno kateri elementi se v seznamu razlikujejo.

.. raw:: latex

    \newpage

.. code-block::
    :caption: pytest izpis ob neuspelem testu pri primerjavi dveh seznamov.

    ==================== test session starts ===================
    platform win32 -- Python 3.8.10, pytest-7.2.0, pluggy
    cachedir: .pytest_cache
    rootdir: C:\dev\git\discord-advertisement-framework
    plugins: asyncio-0.20.3, typeguard-2.13.3
    asyncio: mode=strict
    collected 1 item

    test.py::test_test FAILED                       [100%]

    ========================= FAILURES =========================
    _________________________ test_test ________________________

        def test_test():
    >       assert [1, 2, 3] == [1, 2, 3, 4, 5, 6]
    E       assert [1, 2, 3] == [1, 2, 3, 4, 5, 6]
    E         Right contains 3 more items, first extra item: 4
    E         Full diff:
    E         - [1, 2, 3, 4, 5, 6]
    E         + [1, 2, 3]

    test.py:6: AssertionError


.. raw:: latex

    \newpage


Testiranje ogrodja
---------------------
Testi so v ogrodju razdeljeni po posameznih nivojih in funkcionalnostih. Skoraj vsi testi delujejo sinhrono,
tako da se v testu kliče notranje funkcije posameznih objektov, ki bi jih ogrodje
klicalo v primeru navadnega delovanja. Na tak način so izvedeni, saj je testiranje v navadnem (asinhronem) načinu, kjer se vse
zgodi v :mod:`asyncio` opravilih precej težje, saj bi namreč morali loviti ogrodje ob točno določenih časih, da
bi dejansko testirali to, kar želimo.
Kljub temu obstajata dva testa, ki ogrodje poženeta v navadnem načinu, in sicer sta to testa, ki testirata, če
je perioda pošiljanja prava, in vzporedno preverjata tudi delovanje dinamičnega pridobivanja podatkov.
Kot sem že prej omenil, je pri teh dveh testih potrebno uloviti pravi čas, zato se včasih pojavijo problemi
z Discordovim omejevanjem hitrosti na API klice, kar lahko povzroči, da bo pri pošiljanju sporočila ovojni API nivo
rabil več časa, da naredi zahtevo na API, saj bo čakal, da se omejitev izteče. V tem primeru bo pytest izpisal, da test
ni uspel in ga je potrebno ponoviti. Vsi testi se nahajajo v mapi ``./testing``, relativno na dom projekta.

Avtomatičnih testov običajno ne zaganjam ročno na osebnem računalniku (razen tistih, ki preverjajo delovanje neke
nove funkcionalnosti), temveč se na GitHub platformi avtomatično zaženejo ob vsakem zahtevku za združitev vej (*Pull request*), ko hočem funkcionalnost
s stranske GIT veje prenesti na glavno. Dokler se vsi testi ne izvedejo, GitHub ne bo pustil, da se funkcionalnost prenese na glavno vejo.
