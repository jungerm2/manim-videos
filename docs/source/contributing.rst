Contributing
============

This page explains how to set up your environment to contribute to ``manim-videos``, how to run tests and linters, and how to publish a new version.

Set up environment
------------------

Feel free to use any package manager you like, but in this guide we will use `uv <https://astral-sh.com/uv/>`__ to manage dependencies and virtual environments. To install all development and documentation dependencies, run:

.. code-block:: bash

   uv sync --group dev --group docs

The ``docs`` group contains the dependencies needed to build the documentation (eg: sphinx, etc.), while the ``dev`` group contains the dependencies needed to run the tests and linters.

Linters and Formatters
----------------------

We use `Ruff <https://github.com/astral-sh/ruff>`__ for linting and formatting.

To check for linting errors:

.. code-block:: bash

   uv run ruff check manim_videos tests examples

To format your code:

.. code-block:: bash

   uv run ruff format --extend-select I manim_videos tests examples

Here we use the ``--extend-select I`` flag to also check for import sorting errors.

Running Tests
-------------

We use `pytest <https://docs.pytest.org/en/stable/>`__ for testing:

.. code-block:: bash

   uv run pytest -s -v

Some tests use a harness which renders a scene and checks the output frame-by-frame. If you pass in ``--video-debug`` to pytest, it will save a difference video to pytest's temporary directory for failed test, which you can inspect to see what's going on.

Snapshot Testing
~~~~~~~~~~~~~~~~

Some tests use `syrupy <https://github.com/tophat/syrupy>`__ for snapshot testing. If you've made changes that intentionally change the output of a test, you can update the snapshots:

.. code-block:: bash

   uv run pytest tests/path/to/test::test_name --snapshot-update

The snapshot artifacts will be saved in the ``tests/__snapshots__`` directory, which should be version controlled.

.. warning::

   When updating snapshots, make sure that the changes are intentional and that the new snapshots are correct. You should **always** specify the test for which snapshots need to be updated, otherwise you might update snapshots for tests you didn't intend to.

Building Documentation
----------------------

To build the documentation locally, you'll need the ``docs`` dependency group. If you haven't already, install them:

.. code-block:: bash

   uv sync --group docs

You'll also need the big buck bunny video file, which is used in the quickstart guide, to be in the assets directory. You can download the original video like so: 

.. code-block:: bash

   wget https://archive.org/download/BigBuckBunny/big_buck_bunny_720p_h264.mov \
        -O assets/big_buck_bunny_720p_h264.mov

From the repository root, you can build the documentation with:

.. code-block:: bash

   uv run --group docs sphinx-build -b html -c docs/ docs/source/ docs/build/html/latest

   # Move the generated scenes and slides into the latest directory
   mv docs/build/html/latest/source/* docs/build/html/latest
   rm -rf docs/build/html/latest/source

Once built, you can view the documentation by opening ``docs/build/html/latest/index.html``
in your web browser:

.. code-block:: bash

   uv run python -m webbrowser docs/build/html/latest/index.html

Publishing a new version
------------------------

To publish a new version to `PyPI <https://pypi.org/project/manim-videos/>`__,
first ensure all tests and CI checks have passed on the ``main`` branch:

1. Check that the `GitHub Actions <https://github.com/jungerm2/manim-videos/actions>`__ for the latest commit on ``main`` are passing, these run the linter, tests, and build the documentation.
2. Update the version number in ``manim_videos/__init__.py``.
3. Update the :doc:`changelog` with the new version, date, and changes. Ensure all changes since the last release are documented.
4. Commit and push these changes to the ``main`` branch.
5. Create a new git tag and push it:

   .. code-block:: bash

      git tag -a vX.Y.Z -m "Release vX.Y.Z"
      git push origin vX.Y.Z

The push of a version tag (starting with ``v``) will automatically trigger the GitHub Action to build and publish the package to PyPI. Ensure that this workflow completes successfully, and you're done!
