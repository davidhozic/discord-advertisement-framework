=========================
Dokumentacija
=========================

.. _Python: https://www.python.org


.. _restructuredText: https://docutils.sourceforge.io/rst.html

.. _RTD: https://readthedocs.org/projects/discord-advertisement-framework/

.. |RTD| replace:: Read The Docs


Celoten DAF projekt je odlično dokumentiran. Dokumentacija je na voljo v spletni različici (HTML), kot tudi
lokalni (PDF).

Za vsako novo verzijo projekta, se dokumentacija samodejno zgradi in objavi na `spletni strani <https://daf.davidhozic.com>`_.

Sphinx
=====================
Sistem, ki se uporablja za dokumentiranje projekta se imenuje Sphinx.
Sphinx je popularno orodje med Python_ razvijalci za generiranje dokumentacije v več formatih.
Razvijalcem omogoča ustvarjanje profesionalne dokumentacije za lastne projekte, kar je nuja pri javnih projektih.

Sphinx omogoča enostavno dokumentiranje z berljivo sintakso (restructuredText) z veliko funkcionalnostmi, kjer je ena izmed njih
možnost branja t.i *docstring* :class:`str` objektov iz kode projekta in vključevanju te vsebine v dokumentacijo.
Je zelo konfigurabilno orodje, kjer se konfiguracijo izvede preko ``.py`` datoteke, kamor lahko dodajamo tudi svojo
Python_ kodo.

Primarno Sphinx podpira restructuredText_ za pisanje dokumentov, podpira pa tudi ostale formate, npr. Markdown preko
dodatnih razširitev. Enačbe se lahko piše v jeziku Latex.

.. admonition:: Zanimivost
    :class: hint

    Ta diplomska naloge je pisana ravno s sistemom Sphinx.


reStructuredText
=====================

restructuredText je jezik na katerem deluje :ref:`Sphinx`.
Je priljubljen *markup* jezik, ki se uporablja za dokumentacijo.
Oblikovan je za enostavnost branja, z fokusom na preprostost in moč.
Ena ključnih značilnosti reStructuredTexta je njegova razširljivost, kar omogoča prilagajanje za specifična aplikacijska področja.

Znotraj sintakse reStructuredTexta so na voljo različne vloge in direktive, ki se uporabljajo za dodajanje oblikovanja in strukture dokumentom.
Vloge se uporabljajo za aplikacijo oblikovanja na določene beseda in stavke,
direktive pa so uporabljene za dodajanje nove vsebine v dokument.
Uporabnikom omogočajo ustvarjanje bolj zapletenih in dokumentov,
pri tem pa ohranjajo preprostost in berljivost sintakse.


.. code-block:: reStructuredText
    :caption: reStructuredText direktiva

    .. figure:: img/rickroll.png
        :scale: 50%

        Rickroll image

    .. math:: 
        :label: Derivative of an integral with parameter
        
        \frac{d}{dy}(F(y))=\int^{g_2(y)}_{g_1(y)}f_y dx +
        (f(g_2(y), y)\cdot g_2(y)'{dy} - f(g_1(y), y)\cdot g_1(y)')


.. code-block:: reStructuredText
    :caption: reStructuredText vloga

    :math:`\int 1 dx = x + C`.
    If the above isn't hard enough, the 
    :eq:`Derivative of an integral with parameter`
    is a bit harder.


Dokumentiranje projekta
========================
Projekt DAF je v celoti dokumentiran s Sphinx sistemom.
Na prvem nivoju je dokumentacija razdeljena na:

1. Vodnik - Voden opis kako uporabljati DAF.
2. API referenco - Opis vseh razredov in funkcij, ki jih lahko uporabniki uporabijo v primeru, da pišejo
   svojo kodo, ki uporablja DAF kot paket.

Vodnik je pisan v ``.rst`` datotekah, ki so nastanjene v ``docs/source/guide`` mapi. Dodatno se deli še na vodnik za
GUI in vodnik za jedro.

V nekaterih direktorijah so prisotne datoteke ``dep_local.json``. To so pred-gradne konfiguracijske datoteke, ki dajejo
informacijo o tem iz kje in kam naj se kopirajo dodatne datoteke (ki so skupne drugim delom dokumentacije) in katere
``.py`` skripte naj se izvedejo po kopiranju.
Na primer ``/project root/docs/source/dep_local.json`` datoteka ima sledečo vsebino:

.. literalinclude:: DEP/_dep_local.json
    :caption: Pred-gradna konfiguracijska datoteka

Na podlagi zgornje definicije, se bo bodo v ./DEP mape skopirale slike iz neke zgornje direktorje. Prav tako
se bodo kopirali primeri uporabe jedra DAF. Na koncu se bo izvedla skripta ``generate_autodoc.py``, ki bo na podlagi
:func:`~daf.misc.doc_category` Python_ dekoratorja generirala ``autofunction`` in ``autoclass`` Sphinx direktive, ki bodo
ob gradnji dokumentacije prebrale vsebino *docstring*-ov posameznih razredov in funkcij, ter jo vstavile v dokument.
V primeru da bo ``manual`` parameter nastavljen na ``True`` v 
:func:`~daf.misc.doc_category` dekoratorski funkciji, ne bodo generirane ``autofunction`` direktive, temveč bo skripta
ustvarila ``function`` direktive ter vsebino prekopirala in pretvorila direktno v ``.rst`` datoteko.


.. autofunction:: daf.misc.doc_category


.. code-block:: python
    :caption: Uporaba :func:`~misc.doc_category` dekoratorja.

    @misc.doc_category("Logging reference", path="logging.sql")
    class LoggerSQL(logging.LoggerBASE):
        ...


Generirane ``autofunction`` / ``autoclass`` direktive so del Sphinx-ove vgrajene razširitve :mod:`sphinx.ext.autodoc`.
Razširitev vključi pakete in izbrska *docstring*-e funkcij in razredov, zatem pa ustvari lep opis o funkciji oz. razredu.
V primeru da je v ``autoclass`` direktivi uporabljena ``:members:`` opcija, bo :mod:`~sphinx.ext.autodoc` razširitev
vključila tudi dokumentirane metode in atribute, ki so del razreda.

.. code-block:: restructuredText
    :caption: Avtomatično generirana API referenca

    ============================
    Dynamic mod.
    ============================

    ------------------------
    add_object
    ------------------------
    
    .. Uporabljen je bil manual parameter v doc_category
    .. function:: daf.core.add_object(obj: <class 'daf.client.ACCOUNT'>) -> None
        
        Adds an account to the framework.
        
        
        :param obj: The account object to add
        :type obj: client.ACCOUNT
        
        
        :raises ValueError: The account has already been added to the list.
        :raises TypeError: ``obj`` is of invalid type.


    ============================
    Clients
    ============================

    ------------------------
    ACCOUNT
    ------------------------

    .. autoclass:: daf.client.ACCOUNT
        :members:


Rezultat gornje vsebine:

.. figure:: ./DEP/autodoc_example.png
    :height: 140mm

    Izhod avtomatično generirane API reference.

Iz gornje slike vidimo, da ima :class:`~daf.client.ACCOUNT` dodatno vsebino, ki je ni imel v ``autoclass`` direktivi.
Ta vsebina je bila vzeta iz kode projekta DAF, ki ima sledečo definicijo:

.. code-block:: python
    :caption: Del definicije razreda :class:`~daf.client.ACCOUNT`

    class ACCOUNT:
        """
        .. versionadded:: v2.4

        Represents an individual Discord account.
        
        Each ACCOUNT instance runs it's own shilling task.

        Parameters
        ----------
        token : str
            The Discord account's token
        is_user : Optional[bool] =False
            Declares that the ``token`` is a user account token
            ("self-bot")
        intents: Optional[discord.Intents]=discord.Intents.default()
            Discord Intents
            (settings of events that the client will subscribe to)
        ...
        """
        ...

        @property
        def running(self) -> bool:
            """
            Is the account still running?

            Returns
            -----------
            True
                The account is logged in and shilling is active.
            False
                The shilling has ended or not begun.
            """
            ...

        ...

        @typechecked
        def get_server(
            self,
            snowflake: Union[int, discord.Guild, discord.User, discord.Object]
        ) -> Union[guild.GUILD, guild.USER, None]:
            """
            Retrieves the server based on the snowflake id or discord API object.

            Parameters
            -------------
            snowflake: Union[int, discord.Guild, discord.User, discord.Object]
                Snowflake ID or Discord API object"
            ...
            """
            ...

        ...


Dokumentacija projekta DAF je na voljo na spletni strani RTD_.

RTD_ je spletna platforma za dokumentacijo, ki razvijalcem programske opreme zagotavlja enostaven način za gostovanje,
objavljanje in vzdrževanje dokumentacije za njihove projekte.
Platforma uporabnikom omogoča ustvarjanje profesionalno izgledajoče dokumentacije s preprostostjo in jo ponuja javnosti.
Je odprtokodna in zgrajena na Sphinx-u, močnem orodju za generiranje dokumentacije.

Poleg gostovanja dokumentacije RTD_ ponuja razna orodja, kot so orodje za nadzor različic in napredna funkcionalnost iskanja.
To uporabnikom olajša lažji pregled dokumentacije in zagotavlja, da dokumentacija ostane ažurna.

RTD_ je za DAF projekt konfiguriran, da za vsako novo izdajo verzije preko platforme GitHub, avtomatično zgradi dokumentacijo,
aktivira verzijo in jo nastavi kot privzeto. Na tak način je dokumentacija pripravljena za uporabo praktično takoj ob izdaji verzije.
