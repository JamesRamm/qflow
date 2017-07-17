from celery import group
from qflow import tasks


def run_multiple(control_file_list, tuflow_exe, **kwargs):
    '''
    Create a group for running all models in a given list
    of control files.
    Can then be called like any other celery task
    '''
    task_group = group(
        tasks.run_tuflow.s(
            tcf,
            tuflow_exe,
            run_number=i,
            **kwargs
        ) for i, tcf in enumerate(control_file_list)
    )
    return task_group
