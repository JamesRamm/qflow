'''
Celery tasks for running ANUGA or Tuflow
'''
import time
import subprocess
import glob
import os
import base64
from itertools import chain
from enum import Enum
from celery import Task

from qflow.celery import app
from qflow import utils, checkers

def make_fid(path):
    '''URL-safe base64 encoding of filepaths to transmit over a http api
    '''
    return base64.urlsafe_b64encode(path.encode('utf-8')).decode('utf-8')

def make_process_results(retcode: int, data: dict):
    '''Make a common 'result' dictionary for all tasks
    '''
    if retcode:
        if retcode > 0:
            data['status'] = 'FAILURE'
        elif retcode == 0:
            data['status'] = 'SUCCESS'

    return data

class EventTypes(Enum):
    TUFLOW_MESSAGE = 'task-tuflow-message'
    ANUGA_MESSAGE = 'task-anuga-message'
    VALIDATION_FAIL = 'task-validation-fail'
    FOLDERS_CREATED = 'task-folders-created'

class Anuga(Task):

    def run(self, entry_point, env_name='anuga'):
        '''Run anuga hydro.

        The input python script is executed in a
        conda virtual environment named `env_name`.
        This environment should be configured to run anuga
        '''
        start = time.time()
        # Format the script to override the data directory
        formatter = checkers.AnugaModelFormatter(entry_point)
        results = formatter.format_output_paths()
        proc = utils.execute_in_conda(
            env_name,
            entry_point
        )
        # Poll the process until it has finished
        retcode = proc.poll()
        while retcode is None:
            # Get any output or errors, then wait a little
            # before polling again
            out = proc.stdout.readline()
            err = proc.stderr.readline()

            if out or err:
                self.send_event(
                    EventTypes.ANUGA_MESSAGE.value,
                    stdout=out.decode('utf-8'),
                    stderr=err.decode('utf-8')
                )
            time.sleep(0.5)
            retcode = proc.poll()

        # Move the log file into the results folder
        pth = os.path
        oldpath = pth.join(pth.dirname(entry_point), 'anuga.log')
        if pth.exists(oldpath):
            newpath = pth.join(results, 'anuga.log')
            os.rename(oldpath, newpath)

        end = time.time()
        return make_process_results(
            retcode,
            {'results': make_fid(results), 'runtime': end - start}
        )


class Tuflow(Task):

    def run(
            self,
            tcf_file: str,
            tflow_exe: str,
            mock: bool=False,
            runtime: int=2,
            interval: float=0.5):
        '''Run tuflow for a single control file
        '''
        start = time.time()
        try:
            formatter = checkers.TuflowModelFormatter(tcf_file)
            formatter.validate_model()
        except IOError as error:
            self.send_event(
                EventTypes.VALIDATION_FAIL.value,
                message=str(error)
            )
            return {
                'state': str(EventTypes.VALIDATION_FAIL),
                'data': str(error)
            }

        results, check, log = formatter.format_output_paths()

        # Convert all paths to url-safe id's so they can be passed as URL components
        results = make_fid(results)
        check = make_fid(check)
        log = make_fid(log)

        self.send_event(
            EventTypes.FOLDERS_CREATED.value,
            result_folder=results,
            check_folder=check,
            log_folder=log
        )
        self.runtime = runtime
        self.interval = interval
        retcode = self._run_tuflow(tcf_file, tflow_exe, mock)

        end = time.time()
        return make_process_results(
            retcode,
            {
                'results': results,
                'check': check,
                'log': log,
                'runtime': end - start
            }
        )

    def _mock_tuflow(self):
        '''Pretends to run tuflow
        '''
        runtime = self.runtime
        interval = self.interval
        elapsed = 0
        while elapsed < runtime:
            time.sleep(interval)
            elapsed += 5
            self.send_event(
                EventTypes.TUFLOW_MESSAGE.value,
                stdout='Dummy message, time elapsed {}s'.format(elapsed),
                stderr='Dummy stderr')

    def _run_tuflow(self, tcf_file: str, tflow_exe: str, mock: bool=True):
        '''Run tuflow
        '''
        if mock:
            self._mock_tuflow()
        else:
            # Launch the tuflow application
            # -nmb: dont show windows message boxes
            # tcf file should have Simulation Log Folder == DO NOT USE
            # to supress global logging
            # -od output drive for simulation
            proc = subprocess.Popen(
                [tflow_exe, '-nmb', '-b', tcf_file], stderr=subprocess.PIPE, stdout=subprocess.PIPE)

            # Poll the process until it has finished
            retcode = proc.poll()
            while retcode is None:
                # Get any output or errors, then wait a little
                # before polling again
                out = proc.stdout.readline()
                err = proc.stderr.readline()

                if out or err:
                    self.send_event(
                        'tuflow',
                        stdout=out.decode('utf-8'),
                        stderr=err.decode('utf-8')
                    )
                time.sleep(0.5)
                retcode = proc.poll()
            return retcode


@app.task(bind=True)
def extract_model(self, archive_path: str, model_name: str, directory: str):
    '''Extract a zip file to a new subdirectory of ``directory``, given by
    ``model_name``

    Returns:
        dict: Containing a key ``entrypoints`` which has a list of all *.tcf
            and *.py files found in the root directory.
    '''
    model_directory = utils.extract_model(
        archive_path,
        model_name,
        directory
    )

    # Find all control files/anuga scripts in the model directory
    tcf_pattern = os.path.join(model_directory, '*.tcf')
    py_pattern = os.path.join(model_directory, '*.py')
    entrypoints = chain.from_iterable(
        glob.iglob(pattern) for pattern in (tcf_pattern, py_pattern)
    )

    return {'entrypoints': list(entrypoints)}


@app.task(bind=True)
def validate_model(self, tcf_file: str):
    formatter = checkers.TuflowModelFormatter(tcf_file)
    try:
        formatter.validate_model()
    except IOError as error:
        self.send_event(
            EventTypes.VALIDATION_FAIL.value,
            message=str(error)
        )
        return {
            'state': str(EventTypes.VALIDATION_FAIL),
            'data': str(error)
        }

    return {
        'state': 'SUCCESS',
        'data': {
            'controlFile': tcf_file
        }
    }


@app.task(bind=True, base=Tuflow)
def run_tuflow(self, *args, **kwargs):
    '''Task to execute Tuflow for a given control file.
    See ``Tuflow.__init__`` for supported arguments
    '''
    return super(self.__class__, self).run(*args, **kwargs)


@app.task(bind=True, base=Anuga)
def run_anuga(self, *args, **kwargs):
    '''Task to run an ANUGA python script.
    See ``Anuga.__init__`` for supported arguments
    '''
    return super(self.__class__, self).run(*args, **kwargs)
