#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `qflow` package."""

import unittest
import glob
import os
import shutil
from ship.tuflow import FILEPART_TYPES as fpt

from qflow import tasks, utils, workflow, checkers

def _data_dir():
    # Setup commonly used paths
    root = os.path.dirname(__file__)
    data_dir = os.path.join(root, 'data')
    return root, data_dir

class QFlowTestCase(unittest.TestCase):

    def setUp(self):
        root = os.path.dirname(__file__)
        self._data_dir = os.path.join(root, 'data')
        self._output = os.path.join(root, 'outputs')
        utils.ensure_dir(self._output)

    def tearDown(self):
        shutil.rmtree(self._output)

    def dup_file(self, in_file):
        """Copy a file to the output folder
        """
        fname = os.path.basename(in_file)
        out_file = os.path.join(self._output, fname)
        shutil.copyfile(in_file, out_file)
        return out_file

class TestQflowUtils(QFlowTestCase):

    def test_validation_fail(self):
        tcf_file = os.path.join(self._data_dir, 'bad_paths.tcf')
        fmt = checkers.TuflowModelFormatter(tcf_file)
        self.assertRaises(IOError, fmt.validate_model)

    def test_model_formatting(self):
        """Test the output paths are correctly formatted.
        We expect output paths to be set within the root
        input folder (i.e same folder as TCF file)
        """
        fname = 'M03_5m_001.tcf'
        orig_tcf_file = os.path.join(self._data_dir, fname)
        # We need to make a copy of the tcf file so we dont
        # overwrite the original
        tcf_file = self.dup_file(orig_tcf_file)
        fmt = checkers.TuflowModelFormatter(tcf_file)
        fmt.format_output_paths()

        # Check the tree
        for node in fmt.model.control_file_tree.filter(fpt.RESULT):
            self.assertIn(self._output, node.parameter)

class TestQflowTasks(QFlowTestCase):
    """Tests for `qflow` package."""

    def setUp(self):
        super(TestQflowTasks, self).setUp()

        # Zip up the data for extraction tests
        self._archive = shutil.make_archive(
            os.path.join(self._output, 'test'),
            'zip',
            self._data_dir,
            '.'
        )

    def test_extract(self):
        """Test extracting a model."""
        result = tasks.extract_model(self._archive, 'test_model', self._output)
        self.assertIn('entrypoints', result)
        self.assertEqual(len(result['entrypoints']), 6)

    def test_validate(self):
        """Test a model passes validation"""
        tcf_file = os.path.join(self._data_dir, 'M01_5m_001.tcf')
        result = tasks.validate_model(tcf_file)
        expected = {
            'state': 'SUCCESS',
            'data': {
                'controlFile': tcf_file
            }
        }
        self.assertEqual(result, expected)

    def test_fail_validate(self):
        """Test a model fails validation properly"""
        tcf_file = os.path.join(self._data_dir, 'bad_paths.tcf')
        result = tasks.validate_model(tcf_file)
        self.assertIn('data', result)


    def test_run_tuflow(self):
        """Test the run tuflow task successfully mocks running"""
        # Mock out send_event as it requires the message broker to be
        # running
        tasks.Tuflow.send_event = lambda *args, **kwargs: kwargs

        data_copy = os.path.join(self._output, 'data')
        shutil.copytree(self._data_dir, data_copy)
        tcf_file = os.path.join(data_copy, 'M01_5m_001.tcf')
        result = tasks.run_tuflow(tcf_file, 'tuflow_exe', mock=True, runtime=2, interval=0.5)
        self.assertIn('results', result)

    def test_run_all(self):
        """Test end-to-end: extract model and run all"""
        tasks.Tuflow.send_event = lambda *args, **kwargs: kwargs
        data_copy = os.path.join(self._output, 'data')
        shutil.copytree(self._data_dir, data_copy)

        tcf_list = glob.glob(os.path.join(data_copy, '*.tcf'))

        result = workflow.run_multiple(tcf_list, 'test', mock=True, runtime=0.5, interval=0.1)()
