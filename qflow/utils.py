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
import zipfile
import tarfile
import os

from ship.utils.fileloaders.fileloader import FileLoader
from ship.tuflow import FILEPART_TYPES as fpt
from ship.tuflow.containers import ControlFileNode


def ensure_dir(path: str):
    '''
    Create a directory tree,
    ignore if it already exists
    '''
    try:
        os.makedirs(path)
    except OSError:
        pass


def ensure_path(path: str):
    """
    If the file already exists, rename it
    """
    i = 1
    while os.path.exists(path):
        path = "{}_{}".format(path, str(i).zfill(3))
        i += 1

    return path


def extract_model(archive_path: str, name: str, directory: str):
    '''
    Extract tuflow input data from an archive.
    Archive can be any format supported by zipfile or tarfile std. lib. modules
    '''

    # Create the model directory
    ensure_dir(directory)
    if zipfile.is_zipfile(archive_path):
        archive = zipfile.ZipFile(archive_path)
    else:
        archive = tarfile.open(archive_path)

    # Create the model directory and ensure it is unique
    model_directory = os.path.join(directory, name)
    model_directory = ensure_path(model_directory)

    # Check available space
    stats = os.statvfs(directory)
    freespace = stats.f_frsize * stats.f_bavail
    total_size = sum(info.file_size for info in archive.infolist())

    if freespace <= total_size:
        raise IOError('Not enough space to extract model')

    # Extract then remove the archive
    archive.extractall(path=model_directory)
    archive.close()
    os.remove(archive_path)

    return model_directory

class ModelFormatter(object):
    '''Validate and format a control file

    Validates a models' input files and
    edits the control file to setup output paths
    '''

    def __init__(self, tcf_file: str, run_number: int):

        self.model = FileLoader().loadFile(tcf_file, version=2)
        self.run_number = str(run_number).zfill(3)
        self.tcf_file = tcf_file

    def _create_folder(self, name):
        path = os.path.join(
            self.model.root, name, self.run_number
        )
        ensure_dir(path)
        return path

    def validate_model(self):
        '''
        Validate the referenced files in a tcf_file exist;
        breaks on first failure
        '''
        result = next(self.model.checkPathsExist(), None)
        if result:
            msg = 'The file path in the following statement does not exist:\n\t{}'.format(result[0])
            raise IOError(msg)

    def format_output_paths(self):
        '''
        Automatically set the output paths for the model,
        overriding any that were set in the control file
        '''
        # Setup the output folders
        out_path = self._create_folder("results")
        check_path = self._create_folder("check")
        log_path = self._create_folder("log")

        visited_out_cmd = False
        visited_check_cmd = False
        visited_log_cmd = False
        out_cmd = 'OUTPUT FOLDER'
        check_cmd = 'WRITE CHECK FILES'
        log_cmd = 'LOG FOLDER'

        # Check whether any commands specifying output folders
        # already exist and overwrite them
        for node in self.model.control_file_tree.filter(fpt.RESULT):
            if node.command.upper() == out_cmd:
                visited_out_cmd = True
                node.parameter = out_path
            elif node.command.upper() == check_cmd:
                visited_check_cmd = True
                node.parameter = check_path
            elif node.command.upper() == log_cmd:
                visited_log_cmd = True
                node.parameter = log_path

        # If the commands dont exist, create them
        appender = self.model.control_file_tree.append_statement
        if not visited_out_cmd:
            appender(out_cmd, out_path)
        if not visited_check_cmd:
            appender(check_cmd, check_path)
        if not visited_log_cmd:
            appender(log_cmd, log_path)

        # Overwrite the control file
        with open(self.tcf_file, 'w') as fout:
            self.model.control_file_tree.write(out=fout)

        return out_path, check_path, log_path
