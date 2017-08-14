#!/bin/bash

# Run a celery qflow worker
celery -A qflow worker -l info -Ofair
