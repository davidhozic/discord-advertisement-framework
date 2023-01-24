======================
Unit testing
======================

.. _PyTest: https://docs.pytest.org/

In order to reduce the amount of bugs and broken releases, several unit tests have been made to the project.

All of the tests run on a testing framework called PyTest_.


PyTest testing framework
=========================

Like the name suggests, PyTest is a powerful, feature-rich testing framework for Python.
It is used to write and run tests for software projects,
and is considered to be one of the best testing frameworks available for Python.

One of the main advantages of using pytest is its simplicity. 
Pytest's syntax is easy to understand and use, even for those new to testing or programming.
It also has a lot of built-in functionality, such as test discovery, parameterized tests,
and an advanced assertion introspection system.

Pytest also has excellent support for running tests in parallel,
which can greatly reduce the time it takes to run a large test suite, however there is no parallelism used
in tests created for testing DAF, since Discord's rate limit would cause some tests to fail.

Another big advantage of Pytest is its flexibility.
It can be used to test all types of Python code, including unit tests, integration tests, and functional tests.
Furthermore, Pytest's assertion introspection system makes it easy to understand the failures,
and it also has the capability of providing detailed information about the failures.
The error reporting on PyTest sometimes feels like magic, for example if you were comparing 2 tables 
and one of the tables had 3 more items than the other, PyTest would tell you exactly that and even show you which 3
elements do not match and it will do that with no additional setup, all you need is a simple assert statement like shown below:

.. code-block:: python
    :caption: Pytest table compare assert

    assert [1, 2, 3] == [1, 2, 3, 4, 5, 6]

The above code would result in the following PyTest output (with -vv flag):


.. code-block::
    :caption: Pytest table compare assert result

    ========================================================= test session starts ==========================================================
    platform win32 -- Python 3.8.10, pytest-7.2.0, pluggy-1.0.0 -- C:\dev\git\discord-advertisement-framework\venv\Scripts\python.exe        
    cachedir: .pytest_cache
    rootdir: C:\dev\git\discord-advertisement-framework
    plugins: asyncio-0.20.3, typeguard-2.13.3
    asyncio: mode=strict
    collected 1 item

    test.py::test_test FAILED                                                                                                         [100%]

    =============================================================== FAILURES =============================================================== 
    ______________________________________________________________ test_test _______________________________________________________________ 

        def test_test():
    >       assert [1, 2, 3] == [1, 2, 3, 4, 5, 6]
    E       assert [1, 2, 3] == [1, 2, 3, 4, 5, 6]
    E         Right contains 3 more items, first extra item: 4
    E         Full diff:
    E         - [1, 2, 3, 4, 5, 6]
    E         + [1, 2, 3]

    test.py:6: AssertionError

Furthermore, the framework allows you to easily write reusable fixtures and test functions.

In conclusion, Pytest is a powerful, flexible, and easy-to-use testing framework for Python.
Its simplicity and built-in functionality make it a great choice for writing and running tests 
for any Python software project.
Furthermore, its rich ecosystem of plugins and third-party libraries can help you extend its functionality
to suit your specific needs.






