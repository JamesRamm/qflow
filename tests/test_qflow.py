#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `qflow` package."""


import unittest
import os
import shutil
from ship.tuflow import FILEPART_TYPES as fpt

from qflow import tasks, utils

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
        fmt = utils.ModelFormatter(tcf_file, 0)
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
        fmt = utils.ModelFormatter(tcf_file, 0)
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
        filelist = tasks.extract_model(self._archive, 'test_model', self._output)
        self.assertEqual(len(filelist), 6)

    def test_validate(self):
        """Test a model passes validation"""
        tcf_file = os.path.join(self._data_dir, 'M01_5m_001.tcf')
        result = tasks.validate_model(tcf_file)
        self.assertEqual(result[0], tcf_file)
        self.assertEqual(result[1], 0)

    def test_fail_validate(self):
        """Test a model fails validation properly"""
        tcf_file = os.path.join(self._data_dir, 'bad_paths.tcf')
        with self.assertRaises(IOError):
            tasks.validate_model(tcf_file)

    def test_run_tuflow(self):
        """Test the run tuflow task successfully mocks running"""
        # Mock out send_Event
        tasks.Tuflow.send_event = lambda *args, **kwargs: kwargs

        data_copy = os.path.join(self._output, 'data')
        shutil.copytree(self._data_dir, data_copy)
        tcf_file = os.path.join(data_copy, 'M01_5m_001.tcf')
        tasks.run_tuflow(tcf_file, 'tuflow_exe', mock=True, runtime=2, interval=0.5)
