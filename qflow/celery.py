# -*- coding: utf-8 -*-
"""Main module."""
import os
from celery import Celery
app = Celery(
    'qflow',
    broker=os.environ.get('QFLOW_BROKER', 'pyamqp://guest@localhost//'),
    backend=os.environ.get('QFLOW_BACKEND', 'rpc://'),
    include=['qflow.tasks']

)

if __name__ == '__main__':
    app.start()
