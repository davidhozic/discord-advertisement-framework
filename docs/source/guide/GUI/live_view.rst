==========================
Live view (GUI)
==========================

While the Schema tab allows user to pre-define a schema, the GUI also has a section called *Live view*.

.. figure:: ./images/gui-live-view.png
    :align: center
    :width: 20cm

    Live view tab


Live view allows users to view and update objects that are currently loaded into the framework.
It allows users to modify the original object parameters and then reinitialize the object to use those same
parameters. This can be done by clicking on the *Update* button. Next to the *Update* button, there is a 
*Refresh* button which will reload the GUI with updated values.

If an object does not have a *Update* button, that means the object is not directly supported for live modifications.
In the latter case, users must click the *Save* button, until edit for an object, which supports 
live update, is found. Clicking on *Save* does not reflect changes in the actual framework, but just in the currently
opened window. At the end it is recommended users click on refresh in the main window, which will re-load updated values
to the list.

.. image:: ./images/gui-live-view-edit-account.png
    :align: center
    :width: 15cm


At the top of the *Live view* tab, there's also an *Execute* button with a dropdown menu. It allows you to define a new
:class:`~daf.client.ACCOUNT` object by clicking *Edit* and load the object into the framework directly.
However it is recommended that accounts are defined inside the :ref:`Schema tab (GUI)` and loaded by clicking the
*Load selection to live* button (see :ref:`Loading schema into DAF (GUI)`).

.. image:: ./images/gui-live-view-add-object.png
    :align: center
    :width: 20cm
