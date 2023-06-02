======================
Quickstart (GUI)
======================
This page contains information to quickly getting started with the GUI.

The first thing you need is the library installed, see :ref:`Installation`.

After successful installation, DAF can be run in graphical mode by executing the command ``daf-gui`` command inside the terminal.

.. code-block:: bash

    $ daf-gui

This will open up (after a few seconds) a graphical display you can use to control the framework.

.. image:: ./DEP/daf-gui-front.png
    :scale: 50%
    :align: center


GUI structure
================
The GUI consists of:

- START and STOP buttons starting and stopping DAF's core,
- Connection type selection (see :ref:`Remote control (GUI)`)
- Optional modules tab - Where you can install optional functionallity
- Schema definition tab - Where you can define accounts, guilds, messages & type of logging:
  
  - Accounts - Section for defining your accounts (and guilds and messages).
  - Logging - Section for defining the logging manager used and the detail of the trace (printouts).
  - "Schema" menu button - Allows save or load of GUI data and generation of a Python script which will advertise
    defined data without a GUI. The script interacts directly with DAF core.

- Live view - Viewing and updating objects directly in DAF.
- Output tab for displaying stdout (console) - this is useful for debugging purposes,
- Analytics tab for doing SQL analysis on sent messages:

  - Messages - Used to view message logs stored in a SQL database.
  - Number of messages - Table showing successfully and unsuccessfully sent message counts.
  
- About tab
