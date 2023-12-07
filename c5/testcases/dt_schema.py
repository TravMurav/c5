# SPDX-License-Identifier: GPL-2.0-only
# Copyright (c) 2022 Nikita Travkin <nikita@trvn.ru>

#pylint: disable=missing-function-docstring
#pylint: disable=missing-class-docstring
#pylint: disable=missing-module-docstring
#pylint: disable=attribute-defined-outside-init

import os

import c5
from c5.testcases import TestCase, register_testcase, TestPass, TestWarning

logger = c5.logger

@register_testcase(priority=500)
class DtSchemaTestCase(TestCase):

    desc = "Run dt_binding_check on changed files"

    def _applies(self):
        files = c5.git_get_changed_files(self.commit)
        for file in files:
            if "Documentation/devicetree/bindings/" in file:
                return True

        return False

    def check_yaml(self, filename, pre=""):
        makeargs = ["dt_binding_check", f"DT_SCHEMA_FILES=\"{filename}\""]
        ecode, _, err = c5.linux_make(makeargs)

        msg = err.decode()[:-1]

        if ecode != 0:
            logger.error("Failed to {pre}build!")
            logger.info("%s", msg)
            raise RuntimeError()

        logname = c5.linux_logfile(f"{self.commit[:4]}-dtschema{pre}")
        with open(logname, "w") as logfile:
            logfile.write(msg)
            logger.debug("Build warnings saved in %s", logname)

        return msg

    def prep(self):
        """
        Pre-check all the schema files to find new errors later.
        """
        self.pre_err = ""


        files = []
        for file in c5.git_get_changed_files(self.commit):
            if not os.path.exists(file):
                continue
            if ".yaml" in file:
                files.append(file.replace("Documentation/devicetree/bindings/", ""))

        if len(files) == 0:
            return

        notified = False

        for file in files:
            errs = self.check_yaml(file, pre="pre-")
            if len(errs) > 0:
                self.pre_err += errs
                if not notified:
                    logger.info("YAML pre-check resulted in warnings!")
                    notified = True

                logger.info("%s", errs)


    def run(self):
        files = []
        for file in c5.git_get_changed_files(self.commit):
            if ".yaml" in file:
                files.append(file.replace("Documentation/devicetree/bindings/", ""))

        assert len(files) > 0

        notified = False

        for file in files:
            errs = self.check_yaml(file)
            errs = c5.get_new_lines(self.pre_err, errs)
            if len(errs) > 0:
                if not notified:
                    logger.info("YAML check resulted in new warnings!")
                    notified = True

                logger.info("%s", errs)
