import os
import unittest

from mss.lifecycle import State, LifecycleManager, Lifecycle, Transition
from mss.require import Require
from mss.variable import VString, Hostname


class StateA(State):
    pass


class StateB(State):

    @Require('bar', [VString('foo')])
    def entry(self):
        pass

    @Require('foo1', [VString('bar')])
    def provide1(self, requires):
        pass

    @Require('foo2', [VString('bar1'), VString('bar2')])
    def provide2(self, requires):
        pass

    @Require('foo3', [VString('bar1')])
    @Require('bar3', [VString('foo1')])
    def provide3(self, requires):
        pass

    @Require('foo4', [Hostname('host4')])
    def provide4(self, requires):
        pass


class A(Lifecycle):
    transitions = [Transition(StateA(), StateB())]

    def __init__(self):
        Lifecycle.__init__(self)
        self.init(StateA(), {})


class TestProvideValidation(unittest.TestCase):

    def setUp(self):
        self.lfm = LifecycleManager(modules_dir=os.getcwd(), autoload=False)

    def test_missing_provide_arg(self):
        validation = self.lfm.provide_call_validate("//provide1", requires=[("//bar/foo", "test1")])
        self.assertTrue(validation['errors'])
        self.assertFalse(validation['requires'].entry.bar.variables().foo.error)
        self.assertEqual(validation['provide_args'].provide1.foo1.variables().bar.error, 'bar is required')

    def test_missing_require(self):
        validation = self.lfm.provide_call_validate("//provide1", provide_args=[("//foo1/bar", "test1")])
        self.assertTrue(validation['errors'])
        self.assertEqual(validation['requires'].entry.bar.variables().foo.error, 'foo is required')
        self.assertFalse(validation['provide_args'].provide1.foo1.variables().bar.error)

    def test_valid(self):
        validation = self.lfm.provide_call_validate("//provide1", requires=[("//bar/foo", "test1")], provide_args=[("//foo1/bar", "test1")])
        self.assertEqual(validation['provide_args'].provide1.foo1.variables().bar.error, None)
        self.assertEqual(validation['requires'].entry.bar.variables().foo.error, None)
        self.assertFalse(validation['errors'])

    def test_multiple_variables(self):
        validation = self.lfm.provide_call_validate("//provide2", requires=[("//bar/foo", "test1")], provide_args=[("//foo2/bar1", "test1")])
        self.assertTrue(validation['errors'])
        self.assertEqual(validation['provide_args'].provide2.foo2.variables().bar2.error, 'bar2 is required')
        validation = self.lfm.provide_call_validate("//provide2", requires=[("//bar/foo", "test1")], provide_args=[("//foo2/bar2", "test1")])
        self.assertTrue(validation['errors'])
        self.assertEqual(validation['provide_args'].provide2.foo2.variables().bar1.error, 'bar1 is required')
        validation = self.lfm.provide_call_validate("//provide2", requires=[("//bar/foo", "test1")], provide_args=[("//foo2/bar2", "test1"), ("//foo2/bar1", "test2")])
        self.assertFalse(validation['errors'])

    def test_multiple_requires(self):
        validation = self.lfm.provide_call_validate("//provide3", requires=[("//bar/foo", "test1")], provide_args=[("//foo3/bar1", "test1")])
        self.assertTrue(validation['errors'])
        self.assertEqual(validation['provide_args'].provide3.bar3.variables().foo1.error, 'foo1 is required')
        validation = self.lfm.provide_call_validate("//provide3", requires=[("//bar/foo", "test1")], provide_args=[("//foo3/bar1", "test1"), ("//bar3/foo1", "test2")])
        self.assertFalse(validation['errors'])

    def test_custom_validation(self):
        validation = self.lfm.provide_call_validate("//provide4", requires=[("//bar/foo", "test1")], provide_args=[("//foo4/host4", "44")])
        self.assertTrue(validation['errors'])
        self.assertIn('Incorrect Hostname', validation['provide_args'].provide4.foo4.variables().host4.error)
        validation = self.lfm.provide_call_validate("//provide4", requires=[("//bar/foo", "test1")], provide_args=[("//foo4/host4", "myhost33")])
        self.assertFalse(validation['errors'])


if __name__ == '__main__':
    unittest.main()