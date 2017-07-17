'''
    TuCluster - distributed execution of tuflow models in the cloud
    Copyright (C) 2017  James Ramm

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as published
    by the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''
import time
import subprocess
import glob
import os
from celery import Task, subtask, group

from qflow.celery import app
from qflow import utils


class Tuflow(Task):

    def run(
            self,
            tcf_file: str,
            tflow_exe: str,
            run_number: int=0,
            mock: bool=False,
            runtime: int=2,
            interval: float=0.5):
        '''Run tuflow for a single control file
        '''
        formatter = utils.ModelFormatter(tcf_file, run_number)
        try:
            formatter.validate_model()
        except IOError as error:
            self.send_event(
                'validation-fail',
                stdout=str(error)
            )
            raise

        results, check, log = formatter.format_output_paths()
        self.runtime = runtime
        self.interval = interval
        self._run_tuflow(tcf_file, tflow_exe, mock)
        return results, check, log

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
                'tuflow',
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
                        stdout=out,
                        stderr=err
                    )
                time.sleep(0.5)
                proc.poll()


@app.task(bind=True)
def extract_model(self, archive_path: str, model_name: str, directory: str):
    model_directory = utils.extract_model(
        archive_path,
        model_name,
        directory
    )
    # Find all control files in the model directory
    # The assumption is all .tcf files are in the top level directory
    # and not nested!
    tcf_files = glob.glob(os.path.join(model_directory, '*.tcf'))

    return tcf_files


@app.task(bind=True)
def validate_model(self, tcf_file: str, run_number: int=0):
    formatter = utils.ModelFormatter(tcf_file, run_number)
    try:
        formatter.validate_model()
    except IOError as error:
        self.send_event(
            'validation-fail',
            stdout=str(error)
        )
        raise
    return tcf_file, run_number


@app.task(bind=True, base=Tuflow)
def run_tuflow(self, *args, **kwargs):
    super(self.__class__, self).run(*args, **kwargs)
