==========
QFlow
==========

.. image:: https://codecov.io/gh/JamesRamm/qflow/branch/master/graph/badge.svg
        :target: https://codecov.io/gh/JamesRamm/qflow

.. image:: https://img.shields.io/travis/openfloodmap/qflow.svg
        :target: https://travis-ci.org/openfloodmap/qflow

.. image:: https://pyup.io/repos/github/openfloodmap/qflow/shield.svg
     :target: https://pyup.io/repos/github/openfloodmap/qflow/
     :alt: Updates


QFlow runs Anuga or Tuflow models across a distributed computing cluster.
QFlow manages the distribution of model runs across the cluster automatically, ensuring maximum usage
of your HPC resources and keeping your local computer resources free for your day to day tasks.

QFlow uses Celery & Redis to manage the task queue and runs on Python 3.5+

.. figure:: docs/qflow_arch.png
    :scale: 100 %
    :align: center
    :alt: QFlow conceptual diagram


Quick start
-----------

Follow this to get started using QFlow from the source.

- First install redis and setup conda environments for ANUGA. This can be done by running ``install.sh`` in the ``tools`` directory
- Launch 1 or more celery workers: ``tools/run.sh``


In order to execute an ANUGA script:

.. code-block:: python

        from qflow import tasks

        result = tasks.run_anuga.delay('/path/to/my/script.py')


In the above snippet, ``result`` is a celery ``AsyncResult``. You can check the status of the result by accessing ``result.state``.
If the task has finished, use ``result.result`` to access the task results.

You can easily queue up multiple ANUGA or Tuflow tasks:

.. code-block:: python

        from qflow import tasks

        scripts = ['~/run1.py', '~/run2.py', '~/run3.py']

        results = [tasks.run_anuga.delay(script) for script in scripts]

This script will return immeadiately after adding the tasks to the queue. Your worker(s) will then process each
task until no more are available. You can add another worker at any time and it will start picking up tasks from the queue.

Run with Docker
-----------------

A docker image is provided for QFlow (openfloodmap/qflow).
You can run with ``docker run qflow``.
Note that this image does not run redis - use a tool such as docker-compose to ensure Redis can be accessed from the qflow container.
