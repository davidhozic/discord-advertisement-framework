
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



Avtomatska odkrivanje (angl. discovery) cehov in kanalov
---------------------------------------------------------
Pošiljanje s fiksno periodo dveh ur in avtomatična najdba pridruženih cehov in kanalov na podlagi ReGex vzorca.

.. literalinclude:: ./DEP/Examples/example-autoguild-autochannel.py
    :caption: Avtomatska najdba cehov in kanalov - |PY_EXAMPLE|

.. literalinclude:: ./DEP/Examples/example-autoguild-autochannel.json
    :caption: Avtomatska najdba cehov in kanalov - |SCHEMA_EXAMPLE|



Sledenje cehovskih (pridružnih) povezav
----------------------------------------------
Sledenje trem cehovskim povezavam.

.. literalinclude:: ./DEP/Examples/example-invites-tracking.py
    :caption: Sledenje cehovskih povezav - |PY_EXAMPLE|

.. literalinclude:: ./DEP/Examples/example-invites-tracking.json
    :caption: Sledenje cehovskih povezav - |SCHEMA_EXAMPLE|



Pridružitev novim cehom
----------------------------------------
Pridruževanje največ 15 novim cehom, na podlagi izraza "NFT", ker imajo cehi med 100 in 1000 uporabnikov.


.. literalinclude:: ./DEP/Examples/example-new-guild-join.py
    :caption: Pridružitev novim cehom - |PY_EXAMPLE|

.. literalinclude:: ./DEP/Examples/example-new-guild-join.json
    :caption: Pridružitev novim cehom - |SCHEMA_EXAMPLE|



Oddaljen dostop
----------------------------------------
HTTP strežnik, in GUI shema za povezovanje na ta strežnik.


.. literalinclude:: ./DEP/Examples/example-remote.py
    :caption: Oddaljen dostop - |PY_EXAMPLE|

.. literalinclude:: ./DEP/Examples/example-remote.json
    :caption: Oddaljen dostop - |SCHEMA_EXAMPLE|
