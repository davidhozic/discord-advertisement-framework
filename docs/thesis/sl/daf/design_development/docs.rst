=========================
Dokumentacija
=========================

.. _Python: https://www.python.org


.. _reStructuredText: https://docutils.sourceforge.io/rst.html

.. _RTD: https://readthedocs.org/projects/discord-advertisement-framework/


Za projekt obstaja obsežna dokumentacija, ki se samodejno zgradi ob vsaki novi verziji ogrodja in zatem objavi 
na spletni strani [#daf_web_page]_.

.. [#daf_web_page] Na voljo na: https://daf.davidhozic.com/en/v2.9.x/.

Na voljo je tako v spletni (HTML) kot tudi lokalni obliki (PDF), ki se jo lahko prenese tako, da se na spletni strani dokumentacije
kurzor premakne na levi spodnji del strani nad verzijo dokumentacije in zatem klikne *PDF*.


.. figure:: ./DEP/doc-pdf-download.png
    :height: 8cm

    Prenos PDF dokumentacije


Sphinx
----------------
Sistem, uporabljen za grajenje dokumentacije projekta, se imenuje Sphinx.
Sphinx je popularno orodje med Python razvijalci za generiranje dokumentacije v več formatih.
Razvijalcem omogoča ustvarjanje profesionalne dokumentacije za lastne projekte, kar je nuja pri javnih projektih.

Sphinx omogoča enostavno dokumentiranje z berljivo sintakso (reStructuredText) z veliko funkcionalnostmi, kjer je ena izmed njih
možnost branja t. i. *docstring* besedila iz izvorne kode (angl. *source code*) projekta in vključevanje te vsebine v dokumentacijo.
Je zelo konfigurabilno orodje, kjer se konfiguracijo izvede preko ``.py`` datoteke, kamor lahko dodajamo tudi svojo
Python kodo.

Primarno Sphinx podpira reStructuredText_ za pisanje dokumentov, podpira pa tudi ostale formate, npr. Markdown preko
dodatnih razširitev. Enačbe se lahko piše v jeziku LaTeX.


reStructuredText
-------------------

reStructuredText je jezik, na katerem deluje Sphinx in je priljubljen *markup* jezik za dokumentacijo projektov.

Znotraj sintakse reStructuredTexta so na voljo različne vloge in direktive, ki se uporabljajo za dodajanje oblikovanja in strukture dokumentom.
Vloge se uporabljajo za aplikacijo oblikovanja na določene besede in stavke v isti vrstici,
direktive pa so uporabljene za dodajanje nove vsebine v dokument ali za aplikacijo oblikovanja na večvrstično vsebino :ref:`rst_docutils`.


.. code-block:: reStructuredText
    :caption: reStructuredText direktiva

    .. figure:: img/rickroll.png
        :scale: 50%

        Rickroll image

    .. math:: 
        :label: Derivative of an integral with parameter
        
        \frac{d}{dy}(F(y))=\int^{g_2(y)}_{g_1(y)}f_y dx +
        (f(g_2(y), y)\cdot g_2(y)'{dy} - f(g_1(y), y)\cdot g_1(y)')


.. raw:: latex

    \newpage


.. code-block:: reStructuredText
    :caption: reStructuredText vloga

    :math:`\int 1 dx = x + C`.
    If the above isn't hard enough, the 
    :eq:`Derivative of an integral with parameter`
    is a bit harder.


Organizacija dokumentacije projekta
------------------------------------
Projekt je v celoti dokumentiran s Sphinx sistemom.
Na prvem nivoju je dokumentacija razdeljena na:

1. Vodnik - voden opis, kako uporabljati ogrodje,
2. API referenco - opis vseh razredov in funkcij programskega vmesnika, ki jih lahko uporabniki uporabijo v primeru, da pišejo
   svojo kodo, ki uporablja jedro ogrodja.

Vodnik je pisan ročno v ``.rst`` datotekah, ki so nastanjene v ``/project root/docs/source/guide`` mapi. Dodatno se deli še na vodnik za
GUI in vodnik za jedro.

API referenca je avtomatično generirana iz komentarjev v izvorni kodi ogrodja in jih dodatno deli pod različne kategorije.

V nekaterih direktorijih so prisotne datoteke ``dep_local.json``. To so predgradne konfiguracijske datoteke, ki dajejo
informacijo o tem, iz kje in kam naj se kopirajo dodatne datoteke (ki so skupne drugim delom dokumentacije) in katere
``.py`` skripte naj se izvedejo po kopiranju.
Na primer ``/project root/docs/source/dep_local.json`` datoteka ima sledečo vsebino:


.. raw:: latex

    \newpage


.. literalinclude:: DEP/_dep_local.json
    :caption: Predgradna konfiguracijska datoteka

Na podlagi zgornje definicije se bo bodo v ./DEP mape skopirale slike iz nekega zgornjega direktorja. Prav tako
se bodo kopirali primeri uporabe jedra ogrodja. Na koncu se bo izvedla skripta ``generate_autodoc.py``, ki bo na podlagi
:func:`~daf.misc.doc.doc_category` Python dekoraterja generirala ``autofunction`` in ``autoclass`` Sphinx direktive, ki bodo
ob gradnji dokumentacije prebrale vsebino *docstring*-ov posameznih razredov in funkcij ter jo vstavile v dokument.


.. autofunction:: daf.misc.doc.doc_category


.. code-block:: python
    :caption: Uporaba :func:`~daf.misc.doc.doc_category` dekoratorja.

    @doc.doc_category("Logging reference", path="logging.sql")
    class LoggerSQL(logging.LoggerBASE):
        ...


Iz :func:`~daf.misc.doc.doc_category` generirane ``autofunction``/``autoclass`` direktive so del Sphinx-ove vgrajene razširitve :mod:`sphinx.ext.autodoc`.
Razširitev vključi pakete in izbrska *docstring*-e funkcij in razredov, zatem pa ustvari lep opis o funkciji oz. razredu.
V primeru, da je v ``autoclass`` direktivi uporabljena ``:members:`` opcija, bo :mod:`~sphinx.ext.autodoc` razširitev
vključila tudi dokumentirane metode in atribute, ki so del razreda.

.. code-block:: reStructuredText
    :caption: Iz :func:`~daf.misc.doc.doc_category` generirana direktiva

    .. autoclass:: daf.logging.sql.LoggerSQL
        :members:


.. _auto_doc_example:
.. figure:: ./DEP/autodoc_example.png
    :height: 12cm

    Rezultat autoclass direktive

Iz :numref:`auto_doc_example` lahko vidimo, da ima :class:`~daf.logging.sql.LoggerSQL` dodatno vsebino, ki je ni imel v ``autoclass`` direktivi.
Ta vsebina je bila vzeta iz same izvorne kode razreda.


Dokumentacija projekta je gostovana na spletni strani `Read the Docs (RTD) <RTD_>`_.
RTD je spletna platforma za dokumentacijo, ki razvijalcem programske opreme zagotavlja enostaven način za gostovanje,
objavljanje in vzdrževanje dokumentacije za njihove projekte.
Je odprtokodna platforma, zgrajena na že prej omenjenem Sphinx-u.
Poleg gostovanja dokumentacije ponuja RTD tudi nadzor verzij (angl. *version* control) in določeno avtomatizacijo.
RTD je za projekt konfiguriran tako, da za vsako izdajo nove verzije projekta avtomatično zgradi dokumentacijo,
aktivira verzijo in jo nastavi kot privzeto. Na tak način je dokumentacija pripravljena za uporabo praktično takoj ob izdaji.
Prav tako se dokumentacija zgradi ob vsakem zahtevku za združitev vej (angl. Pull request) na GitHub platformi.


