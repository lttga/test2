***************
Developer Guide
***************

Create environment
==================

To create environment please execute following commands:

.. code-block:: bash

    git clone https://github.com/open-contracting/spoonbill
    cd spoonbill
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -e .

Please make sure you have `pre-commit <https://pre-commit.com/>`_ installed.

Running the tests
=================

After following the installation above, run:

.. code-block:: bash

    pytest

Running the linters
===================

To run the linters execute:

.. code-block:: bash

    pre-commit run -a

Commiting changes
=================

Make sure your commit message follows `conventional commit specification <https://www.conventionalcommits.org/en/v1.0.0/>`_.

Versioning and CHANGELOG
========================

This library is versioned and a changelog is kept in the CHANGELOG.rst file. See that file for more.

Any pull request to this library should include updating the CHANGELOG.rst file.

PyPi
====

This package is published on `pypi.org <https://pypi.org/project/spoonbill/>`_
