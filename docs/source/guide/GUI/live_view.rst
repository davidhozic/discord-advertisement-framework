==========================
Live view (GUI)
==========================

While the Schema tab allows user to pre-define a schema, the GUI also has a section called Live view.

Live view allows users to view and update objects that are actually (real-time) added to the framework.
It allows users to modify the original object parameters and then reinitialize the object to use those same
parameters. This can be done by clicking on the ``Update`` button.

If object does not have a ``Update`` button, that means the object is not directly supported for live modifications.
In the later case, users must click the ``Save`` button, until edit for an object, which supports 
live update, is found. Clicking on ``Save`` does not reflect changes in the actual framework, but just in the currently
opened window. At the end it is recommended users click on refresh in the main window, which will re-load updated values
to the list.

