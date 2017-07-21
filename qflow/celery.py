# -*- coding: utf-8 -*-
"""Main module."""
import os
from celery import Celery

os.environ.setdefault('CELERY_CONFIG_MODULE', 'qflow.celeryconfig')

app = Celery(
    'qflow',
    include=['qflow.tasks']
)
app.config_from_envvar('CELERY_CONFIG_MODULE')
