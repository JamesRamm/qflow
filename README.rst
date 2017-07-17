=====
QFlow
=====

.. image:: https://codecov.io/gh/JamesRamm/qflow/branch/master/graph/badge.svg
        :target: https://codecov.io/gh/JamesRamm/qflow

.. image:: https://img.shields.io/travis/JamesRamm/qflow.svg
        :target: https://travis-ci.org/JamesRamm/qflow

.. image:: https://pyup.io/repos/github/JamesRamm/qflow/shield.svg
     :target: https://pyup.io/repos/github/JamesRamm/qflow/
     :alt: Updates


QFlow is a library for running Tuflow models across a distributed task queue.
It uses Celery for the task queue and runs on Python 3.5+

* License: AGPL

Quick start
-----------

- Setup the message broker for celery (e.g. RabbitMQ)
- Launch the celery server: ``python -m qflow.qflow``
- Launch 1 or more celery workers: ``celery -A qflow worker -l info`` (run this in the directory above the qflow package)

You can now use the tasks in your python application.
For example, you can start models running on the cluster for a number of TCF files like this:

.. code-block:: python

        from qflow import tasks

        result_list = [
            tasks.run_tuflow.delay(control_file, 'tuflow.exe') for control_file in control_file_list
        ]

