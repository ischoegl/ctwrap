#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""rudimentary unit tests
"""

import unittest
from pathlib import Path
import subprocess
import pint.quantity as pq
import importlib

import ctwrap as cw


PWD = Path(__file__).parents[0]
ROOT = PWD.parents[0]
EXAMPLES = '{}'.format(ROOT / 'yaml')


class TestLegacy(unittest.TestCase):

    def test_handler(self):
        with self.assertWarnsRegex(PendingDeprecationWarning, "Old implementation"):
            sh = cw.SimulationHandler.from_yaml('legacy.yaml', path=PWD)
        self.assertIsInstance(sh.tasks, dict)
        self.assertIn('initial.phi_0.4', sh.tasks)


class TestWrap(unittest.TestCase):

    _module = cw.modules.minimal
    _task = 'sleep_0.4'
    _yaml = 'minimal.yaml'
    _hdf = None
    _path = None

    def tearDown(self):
        if self._hdf:
            [hdf.unlink() for hdf in Path(EXAMPLES).glob('*.h5')]
            [hdf.unlink() for hdf in Path(ROOT).glob('*.h5')]

    def test_simulation(self):
        sim = cw.Simulation.from_module(self._module)
        self.assertIsNone(sim.data)
        sim.run()
        self.assertIsInstance(sim.data, dict)
        for key in sim.data.keys():
            self.assertIn('defaults', key)

    def test_handler(self):
        sh = cw.SimulationHandler.from_yaml(self._yaml, path=EXAMPLES)
        self.assertIsInstance(sh.tasks, dict)
        self.assertIn(self._task, sh.tasks)

    def test_serial(self):
        sim = cw.Simulation.from_module(self._module)
        sh = cw.SimulationHandler.from_yaml(self._yaml, path=EXAMPLES)
        self.assertTrue(sh.run_serial(sim))

        if self._hdf:
            hdf = Path(EXAMPLES) / self._hdf
            self.assertTrue(hdf.is_file())

    def test_parallel(self):
        sim = cw.Simulation.from_module(self._module)
        sh = cw.SimulationHandler.from_yaml(self._yaml, path=EXAMPLES)
        self.assertTrue(sh.run_parallel(sim))

        if self._hdf:
            hdf = Path(EXAMPLES) / self._hdf
            self.assertTrue(hdf.is_file())

    def test_commandline(self):
        cmd = 'ctwrap'
        if isinstance(self._module, str):
            name = self._module
        else:
            name = self._module.__name__.split('.')[-1]
            if self._path:
                name = "{}".format(Path(self._path) / '{}.py'.format(name))
        yaml = "{}".format(Path(EXAMPLES) / self._yaml)
        pars = [name, yaml, '--parallel']

        self.maxDiff = None
        process = subprocess.Popen([cmd] + pars,
                     stdout=subprocess.PIPE,
                     stderr=subprocess.PIPE)
        _, stderr = process.communicate()
        self.assertEqual(stderr.decode(), '')

        if self._hdf:
            hdf = Path(EXAMPLES) / self._hdf
            self.assertTrue(hdf.is_file())


class TestCustom(TestWrap):

    _module = importlib.import_module('custom')
    _path = 'tests'


class TestPath(TestWrap):

    _module = '{}'.format(PWD / 'custom.py')


class TestIgnition(TestWrap):

    _module = cw.modules.ignition
    _task = 'initial.phi_0.4'
    _yaml = 'ignition.yaml'
    _hdf = 'ignition.h5'


class TestAdiabaticFlame(TestWrap):

    _module = cw.modules.adiabatic_flame
    _task = 'upstream.phi_0.4'
    _yaml = 'adiabatic_flame.yaml'
    _hdf = 'adiabatic_flame.h5'

    def test_commandline(self):
        # disable until deprecationwarnings are fixed
        pass


if __name__ == "__main__":
    unittest.main()
