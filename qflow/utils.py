'''
General utility functions
'''
import smtplib
import zipfile
import tarfile
import os
import shlex
from subprocess import Popen, PIPE


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

def execute_in_conda(env_name, script):
    '''Execute Python code in a conda environment, return its stdout and stderr.'''

    # We CD into the directory of the script as anuga often expects data files to be co-located
    # etc..
    command_template = '/bin/bash -c "cd {} && source activate {} && python {}"'
    command = shlex.split(command_template.format(os.path.dirname(script), env_name, script))
    process = Popen(command, stdout=PIPE, stderr=PIPE)
    return process


def extract_model(archive_path: str, name: str, directory: str):
    '''
    Extract input data from an archive.
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


class Emailer:
    '''Send emails via SMTP
    '''
    def __init__(self, host, port, user, password):
        self._host = host
        self._port = port
        self._user = user
        self._pwd = password

    def send_email(self, recipient, subject, body):
        '''Send an email via smtp
        '''
        recipients = recipient if type(recipient) is list else [recipient]

        # Prepare actual message
        message = "From: {}\nTo: {}\nSubject: {}\n\n{}".format(
            self._user,
            ", ".join(recipients),
            subject,
            body
        )
        server = smtplib.SMTP(self._host, self._port)
        server.ehlo()
        server.starttls()
        server.login(self._user, self._pwd)
        server.sendmail(self._user, recipients, message)
        server.close()
