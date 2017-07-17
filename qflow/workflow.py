from celery import chain, chord
from qflow import tasks


def extract_and_run_models(archive_path, model_name, directory, tuflow_exe):
    '''
    Extract an archive and run all models within it
    '''
    process_list = (
        tasks.extract_model.s(archive_path, model_name, directory) |
        tasks.dmap.s(tasks.run_tuflow.s(tuflow_exe))
    )

    return process_list
