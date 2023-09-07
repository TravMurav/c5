# SPDX-License-Identifier: GPL-2.0-only
# Copyright (c) 2022 Nikita Travkin <nikita@trvn.ru>

#pylint: disable=missing-function-docstring
#pylint: disable=missing-class-docstring
#pylint: disable=missing-module-docstring

import b4

import c5
from c5.testcases import TestCase, register_testcase, TestPass, TestWarning

logger = c5.logger

@register_testcase(priority=100)
class CheckPatchTestCase(TestCase):

    desc = "Run checkpatch.pl"

    def run(self):
        kernel_base = b4.git_get_toplevel()
        if kernel_base is None:
            raise RuntimeError()

        checkpatchargs = ["./scripts/checkpatch.pl", "--git", "HEAD", "--terse", "--showfile", "--no-summary"]
        if c5.color:
            checkpatchargs.append("--color=always")
        ecode, out, err = c5.run_command(checkpatchargs, rundir=kernel_base)

        message = out.decode()

        if ecode == 0:
            if len(message) > 0:
                logger.info("%s", message[:-1])
            return TestPass()
        elif ecode == 1:
            logger.info("Checkpatch found something...")
            logger.info("%s", message[:-1])
            return TestWarning()
        else:
            raise RuntimeError()
