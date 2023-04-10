======================
Quickstart (GUI)
======================
This page contains information to quickly getting started with the GUI.

The first thing you need is the library installed, see :ref:`Installation`.

After successful installation, DAF can be run in graphical mode by executing the command ``daf-gui`` command inside the terminal.

.. code-block:: bash

    $ daf-gui

This will open up (after a few seconds) a graphical display you can use to control the framework.

.. image:: ./DEP/images/daf-gui-front.png
    :scale: 70%
    :align: center


GUI structure
================
The GUI consists of:

- START / STOP buttons for starting and stopping the framework,
- Schema definition tab - Where you can define accounts, guilds, messages & type of logging:
  
  - Accounts - Section for defining your accounts (and guilds and messages).
  - Logging - Section for defining the logging manager used and the detail of the trace (printouts).
  - "Load/Save/Generate" menu button - Allows you to save or load the GUI state & to generate a Python script that
    will shill the configured items without the graphical interface.


- Output tab for displaying stdout (console) - this is useful for debugging purposes,
- Analytics tab for doing SQL analysis on sent messages,
- About tab
