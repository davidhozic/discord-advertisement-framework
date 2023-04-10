======================
Analytics (GUI)
======================

.. caution::

    Analytics are currently **only** available if SQL is used for logging (:class:`~daf.logging.sql.LoggerSQL`).


.. note::

    In the **future**, invite link tracking is also to be implemented.


.. image:: ./images/gui-analytics-tab.png
    :align: center
    :width: 20cm


Both daf's core and GUI provide a way to retrieve logs of sent messages from a SQL database.

Analytics are available in the *Analytics* tab of the GUI and contain 2 labeled frames.



Messages frame
====================== 
Messages frame allow retrieval of message logs and their display though the object edit window.

.. image:: ./images/gui-analytics-message-frame.png
    :align: center
    :width: 20cm


The frame contains a dropdown w/ an edit button for defining parameters and 3 buttons.

The edit button will open up an object edit window where you can define your query parameters. After you click save,
the parameters will get save into the dropdown menu. When using the *Get logs* button, 
these parameters will be considered. Use *Help* inside the definition window to get insight on the parameters.

The 3 buttons allow you to retrieve, view and convert data:

1. Get logs - retrieves the logs from the database and inserts them into the list at the bottom,

   .. image:: ./images/gui-analytics-message-frame-get-logs.png
       :align: center
       :width: 20cm

2. View log - opens an object edit window which can be used to inspect the log's content (read-only)

   .. image:: ./images/gui-analytics-message-frame-view-log.png
       :align: center
       :height: 10cm

3. Save selected as JSON - saves the logs selected from the list into a JSON file, the output contains a list of logs
   with attributes ``type`` which specifies the datatype and ``data`` which is the actual JSON data of saved object.


Number of messages frame
=========================

Number of messages frame can be used to count the amount of successful / failed message attempts into a 
specific guild from specific author on the selected day / month / year.

.. image:: ./images/gui-analytics-num-message-frame.png
    :align: center
    :width: 20cm

The frame contains one dropdown w/ edit button which can be used to configure the query and one *Calculate*
button.

Clicking on *Edit* will open up a object definition window where you can define the parameters.
Use *Help* inside the definition window to get insight on the parameters.

Clicking on *Calculate* does the SQL analysis and inserts the result into the table below.

.. image:: ./images/gui-analytics-num-message-frame-calc.png
    :align: center
    :width: 20cm
  

