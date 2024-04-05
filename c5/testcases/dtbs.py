# SPDX-License-Identifier: GPL-2.0-only
# Copyright (c) 2022 Nikita Travkin <nikita@trvn.ru>

#pylint: disable=missing-function-docstring
#pylint: disable=missing-class-docstring
#pylint: disable=missing-module-docstring
#pylint: disable=attribute-defined-outside-init

import os
import re

import b4

import c5
from c5.testcases import TestCase, register_testcase, TestPass, TestWarning

logger = c5.logger

@register_testcase(priority=700)
class DtbsTestCase(TestCase):

    desc = "Run dtbs_check on changed files"

    @classmethod
    def _register_args(cls, parser):
        """Register testcase cmdline args."""
        cls.add_arg(parser, "filter", action="store", help=f"Filter to use when looking up which dtb files to check.")

    def _applies(self):
        files = c5.git_get_changed_files(self.commit)
        for file in files:
            if ".dts" in file:
                return True

        return False

    def check_dtbs(self, filenames, pre=""):
        makeargs = ["CHECK_DTBS=y", "W=1"] + filenames
        ecode, _, err = c5.linux_make(makeargs)

        msg = err.decode()[:-1]

        if ecode != 0:
            logger.error("Failed to build {pre}!")
            logger.info("%s", msg)
            raise RuntimeError()

        logname = c5.linux_logfile(f"{self.commit[:4]}-dtbs{pre}")
        with open(logname, "w") as logfile:
            logfile.write(msg)
            logger.debug("Build warnings saved in %s", logname)

        return msg

    def target_list(self):
        files = c5.git_get_changed_files(self.commit)

        arches = []
        vendors = []

        pat = re.compile(r"arch/(?P<arch>\w+)/boot/dts/(?P<vendor>\w+)/(?P<source>[\w-]+\.dtsi?)")

        for file in files:
            if ".dts" not in file:
                continue

            match = pat.search(file)
            arches.append(match.group("arch"))
            vendors.append(match.group("vendor"))

        if len(set(arches)) != 1:
            print(f"{arches=}")
            raise NotImplementedError()

        kernel_base = b4.git_get_toplevel()
        targets = []

        pattern = self.get_arg("filter")
        if pattern is None:
            pattern = ""

        pat = re.compile(r"(?P<target>" + pattern + r"[\w-]+\.dtb)")

        for vendor in vendors:
            makefile = f"{kernel_base}/arch/{arches[0]}/boot/dts/{vendor}/Makefile"
            if not os.path.exists(makefile):
                raise RuntimeError()

            lines = []
            with open(makefile, "r") as file:
                lines = file.read().splitlines()

            for line in lines:
                match = pat.search(line)
                if match is None:
                    continue

                target = match.group("target")
                if target is None:
                    continue

                if arches[0] != "arm":
                    target = f"{vendor}/{target}"

                targets.append(target)

        return list(set(targets))


    def prep(self):
        ecode, _, err = c5.linux_make(["allyesconfig"])
        assert ecode == 0

        targets = self.target_list()
        logger.debug("We have %d dtbs to pre-check...", len(targets))
        # they will always have warnings, save but print nothing...
        self.pre_err =  ""
        if len(targets) > 0:
            self.pre_err = self.check_dtbs(targets, pre="pre")

    def undisable_all(self):
        changed_files = c5.git_get_changed_files(self.commit)
        for file in changed_files:
            if ".dts" not in file:
                continue
            if not os.path.exists(file):
                continue
            sedargs = ["sed", "-i", "/status.*\(disabled\|reserved\)/d", file]
            ecode, _, _ = c5.run_command(sedargs)
            assert ecode == 0

    def run(self):
        targets = self.target_list()
        errs = self.check_dtbs(targets)
        errs = c5.get_new_lines(self.pre_err, errs)
        if len(errs) > 0:
            logger.info("DTB check resulted in new warnings!")
            logger.info("%s", errs)

        # The checker ignores disabled nodes. Remove status=disabled from changed files and run again.

        # pre-check: soft-revert the commit and get a log.
        gitargs = ["revert", "--no-commit", self.commit]
        ecode, _ = b4.git_run_command(None, gitargs)
        assert ecode == 0
        gitargs = ["reset"]
        ecode, _ = b4.git_run_command(None, gitargs)
        assert ecode == 0

        self.undisable_all()

        old_errs = self.check_dtbs(targets, "enall-pre")

        gitargs = ["checkout", "."]
        ecode, _ = b4.git_run_command(None, gitargs)
        assert ecode == 0
        self.undisable_all()

        new_errs = self.check_dtbs(targets, "enall")

        errs = c5.get_new_lines(old_errs, new_errs)
        if len(errs) > 0:
            logger.info("DTB check without disables resulted in new warnings!")
            logger.info("%s", errs)

        gitargs = ["checkout", "."]
        ecode, _ = b4.git_run_command(None, gitargs)
        assert ecode == 0
