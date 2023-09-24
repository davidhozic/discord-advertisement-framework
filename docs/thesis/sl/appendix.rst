
==================
Priloge
==================


Dodatne slike
===============

.. raw:: latex

    \newpage


.. _daf-gui-analytics-tab-rotated:
.. figure:: ./DEP/daf-gui-analytics-tab-rotated.png
    :height: 20.5cm

    Zavihek *Analytics*


.. _fig-gui-front:
.. figure:: ./DEP/daf-gui-front-rotated.png
    :height: 20.5cm

    Grafični vmesnik (*Schema definition* zavihek)


Primeri konfiguracije ogrodja
==============================

.. |PY_EXAMPLE| replace:: jedro ogrodja
.. |SCHEMA_EXAMPLE| replace:: GUI shema


Pošiljanje sporočila z naključno periodo
--------------------------------------------
Pošiljanje tekstovnega sporočila s periodo naključno med 1 uro in 2 urama, z začetkom pošiljanja
13.07.2023 00:00:00, kjer se sporočilo pošlje petkrat.

.. _example-text-message-randomized-period:
.. literalinclude:: ./DEP/Examples/example-text-message-randomized-period.py
    :caption: Pošiljanje sporočila z naključno periodo - |PY_EXAMPLE|

.. literalinclude:: ./DEP/Examples/example-text-message-randomized-period.json
    :caption: Pošiljanje sporočila z naključno periodo - |SCHEMA_EXAMPLE|



Avtomatsko odkrivanje (angl. *discovery*) cehov in kanalov
-----------------------------------------------------------
Pošiljanje s fiksno periodo dveh ur in avtomatično odkrivanje pridruženih cehov in kanalov na podlagi RegEx vzorca.

.. literalinclude:: ./DEP/Examples/example-autoguild-autochannel.py
    :caption: Avtomatsko odkrivanje cehov in kanalov - |PY_EXAMPLE|

.. literalinclude:: ./DEP/Examples/example-autoguild-autochannel.json
    :caption: Avtomatsko odkrivanje cehov in kanalov - |SCHEMA_EXAMPLE|


Oddaljen dostop
----------------------------------------
HTTP strežnik in GUI shema za povezovanje na ta strežnik.


.. literalinclude:: ./DEP/Examples/example-remote.py
    :caption: Oddaljen dostop - |PY_EXAMPLE|

.. literalinclude:: ./DEP/Examples/example-remote.json
    :caption: Oddaljen dostop - |SCHEMA_EXAMPLE|
