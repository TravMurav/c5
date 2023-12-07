# SPDX-License-Identifier: GPL-2.0-only
# Copyright (c) 2022 Nikita Travkin <nikita@trvn.ru>

#pylint: disable=missing-function-docstring
#pylint: disable=missing-module-docstring

import argparse

import c5

logger = c5.logger

_testcases = []

class TestCase:
    """A patch test case"""

    def __init__(self, commit=None, cmdargs=None):
        self.commit = commit
        self._cmdargs = vars(cmdargs)

    def applies(self):
        """Does this testcase apply to the top commit?"""
        if self.get_arg("skip"):
            return False

        return self._applies

    def _applies(self):
        return True # Never skip by default

    def prep(self):
        """Do whatever is necessary to prepare for the testing"""

    def run(self):
        """Do whatever is necessary to test the top commit"""
        raise NotImplementedError()

    def get_arg(self, name):
        """Get the argument value"""
        name = type(self).__name__.replace("TestCase", "").lower() + "_" + name
        return self._cmdargs[name]

    @classmethod
    def add_arg(cls, parser : argparse.ArgumentParser, name, action="store_true", default=False, help=None):
        """Add an argument for this testcase"""
        name = "--" + cls.__name__.replace("TestCase", "").lower() + "_" + name
        parser.add_argument(name, action=action, default=default, help=help)

    @classmethod
    def register_args(cls, parser : argparse.ArgumentParser):
        """Register testcase cmdline args."""
        cls.add_arg(parser, "skip", help=f"skip the '{cls.__name__.replace('TestCase', '')}' testcase")
        cls._register_args(parser)

    @classmethod
    def _register_args(cls, parser):
        pass # Nothing extra by default


class TestResult:
    """Result of the test run"""

    severity = None

    def __init__(self, msg=None):
        self.msg = msg

class TestSkip(TestResult):
    """Test passed with no warnings or errors"""
    severity = 0

class TestPass(TestResult):
    """Test passed with no warnings or errors"""
    severity = 1

class TestWarning(TestResult):
    """Test passed with no warnings or errors"""
    severity = 2

class TestFail(TestResult):
    """Test passed with no warnings or errors"""
    severity = 3


def register_testcase(priority=1000):
    """Register a TestCase.
       The bigger the priority value the later the test will run.
    """
    def _register(cla):
        _testcases.append((cla, priority))
        return cla
    return _register


def get_testcases():
    return [ tup[0] for tup in sorted(_testcases, key=lambda tup: tup[1])]

def register_testcase_args(parser):
    cases = get_testcases()

    for case in cases:
        case.register_args(parser)

# https://stackoverflow.com/a/5135444
def _import_package_files():
    """ Dynamically import all the public attributes of the python modules in this
        file's directory (the package directory) and return a list of their names.
    """
    import os
    exports = []
    globals_, locals_ = globals(), locals()
    package_path = os.path.dirname(__file__)
    package_name = os.path.basename(package_path)

    for filename in os.listdir(package_path):
        modulename, ext = os.path.splitext(filename)
        if modulename[0] != '_' and ext in ('.py', '.pyw'):
            subpackage = '{}.{}'.format(package_name, modulename) # pkg relative
            module = __import__(subpackage, globals_, locals_, [modulename])
            modict = module.__dict__
            names = (modict['__all__'] if '__all__' in modict else
                     [name for name in modict if name[0] != '_'])  # all public
            exports.extend(names)
            globals_.update((name, modict[name]) for name in names)

    return exports

if __name__ != '__main__':
    __all__ = ['__all__'] + _import_package_files()  # '__all__' in __all__
