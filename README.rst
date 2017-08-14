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

- Install Redis (https://redis.io/).
- ``pip install -r requirements.txt`` to install the dependencies
- Setup a conda environment for running ANUGA: ``create_anuga_env.sh``. (Note: This requires conda; https://conda.io/miniconda.html)
- Launch 1 or more celery workers: ``celery -A qflow worker -l info -Ofair`` (run this in the directory above the qflow package)


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
