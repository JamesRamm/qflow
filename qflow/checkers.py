'''
Validation and formatting for Anuga & Tuflow entry point scripts.
'''
import os

from ship.utils.fileloaders.fileloader import FileLoader
from ship.tuflow import FILEPART_TYPES as fpt

from qflow.utils import ensure_dir

class TuflowModelFormatter(object):
    '''Validate and format a control file

    Validates a models' input files and
    edits the control file to setup output paths
    '''

    def __init__(self, tcf_file: str):

        self.model = FileLoader().loadFile(tcf_file, version=2)
        self.tcf_file = tcf_file

    def _create_folder(self, root, name):
        i = 0
        while True:
            path = os.path.join(
                root,
                name,
                str(i).zfill(3)
            )
            if os.path.isdir(path):
                i += 1
            else:
                break

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
        out_path = self._create_folder(self.model.root, "results")
        check_path = self._create_folder(self.model.root, "check")
        log_path = self._create_folder(self.model.root, "log")

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


class AnugaModelFormatter(TuflowModelFormatter):
    '''Format an ANUGA script.
    Currently all this does is override the ``datadir``
    location.
    '''
    def __init__(self, script: str):
        self._script = script

    def format_output_paths(self):
        '''Override the ``set_datadir`` method in the anuga script
        '''
        # Create the results folder
        results_path = self._create_folder(os.path.dirname(self._script), 'results')

        # To set the output data directory in anuga, the user
        # must create an instance of ``anuga.Domain`` and call the
        # ``set_datadir`` method of this instance.
        # Here we will search for this method call and replace it
        with open(self._script) as fin:
            contents = fin.readlines()

        added_default = False
        default_datadir_string = "anuga.config.default_datadir='{}'\n".format(results_path)
        for i, line in enumerate(contents):
            if 'set_datadir' in line:
                instance_name = line.split('.set_datadir')[0]
                contents[i] = "{}.set_datadir('{}')\n".format(instance_name, results_path)

            # This is our fail safe - if set_datadir isnt called,
            #  it will use the default datadir. We will override this at the
            # top of the script
            if 'import anuga' in line:
                # insert the override before the next line
                contents.insert(i+1, default_datadir_string)
                added_default = True

        # It is not _totally_ beyond the realm of possibility that anuga is *not* imported in the
        # script. E.g. the script could just call functions in another user uploaded file.
        # This is unlikely, but lets be extra sure.
        if not added_default:
            contents.insert(0, "import anuga\n{}".format(default_datadir_string))

        # Overwrite the script
        with open(self._script, 'w') as fout:
            fout.writelines(contents)

        return results_path
