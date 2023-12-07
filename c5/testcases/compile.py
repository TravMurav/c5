# SPDX-License-Identifier: GPL-2.0-only
# Copyright (c) 2023 Nikita Travkin <nikita@trvn.ru>

#pylint: disable=missing-function-docstring
#pylint: disable=missing-class-docstring
#pylint: disable=missing-module-docstring
#pylint: disable=attribute-defined-outside-init

import os
import re

import b4

import c5
from c5.testcases import TestCase, register_testcase
logger = c5.logger

@register_testcase(priority=700)
class CompileTestCase(TestCase):

    desc = "Compile changed C source files"

    def _applies(self):
        files = c5.git_get_changed_files(self.commit)
        for file in files:
            if ".c" in file:
                return True

        return False

    def check_c_src(self, filename, pre=""):
        makeargs = [ filename.replace(".c", ".o") ]
        ecode, _, err = c5.linux_make(makeargs)
        msg = err.decode()[:-1]

        if ecode != 0:
            logger.error(f"Failed to {pre}build!")
            logger.info("%s", msg)
            raise RuntimeError()

        logname = c5.linux_logfile(f"{self.commit[:4]}-compile{pre}")
        with open(logname, "w") as logfile:
            logfile.write(msg)
            logger.debug("Build warnings saved in %s", logname)

        return msg

    def run(self):
        ecode, _, err = c5.linux_make(["allyesconfig"])
        assert ecode == 0

        files = []
        for file in c5.git_get_changed_files(self.commit):
            if not os.path.exists(file):
                continue
            if ".c" in file:
                files.append(file)

        if len(files) == 0:
            return

        notified = False

        for file in files:
            errs = self.check_c_src(file)
            if len(errs) > 0:
                self.pre_err += errs
                if not notified:
                    logger.info("Compile check resulted in warnings!")
                    notified = True

                logger.info("%s", errs)

