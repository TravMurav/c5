# SPDX-License-Identifier: GPL-2.0-only
# Copyright (c) 2022 Nikita Travkin <nikita@trvn.ru>

import argparse
import logging
import sys

import c5
import c5.test
import c5.testcases

logger = c5.logger

def cmd_test(cmdargs):
    c5.test.main(cmdargs)

def setup_parser():
    parser = argparse.ArgumentParser(
        prog='c5',
        description='A tool to smoketest a series of patches',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument('-d', '--debug', action='store_true', default=False,
                        help='Add more debugging info to the output')
    parser.add_argument('-q', '--quiet', action='store_true', default=False,
                        help='Output critical information only')

    subparsers = parser.add_subparsers(help='sub-command help', dest='subcmd')

    # c5 test
    sp_test = subparsers.add_parser('test', help='Run tests on the git tree')
    sp_test.set_defaults(func=cmd_test)

    c5.testcases.register_testcase_args(sp_test)

    return parser

class CustomFormatter(logging.Formatter):

    dark = "\x1b[30;20m"
    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format = "%(message)s"

    FORMATS = {
        logging.DEBUG: dark + format + reset,
        logging.INFO: grey + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


def cmd():
    parser = setup_parser()
    cmdargs = parser.parse_args()
    logger.setLevel(logging.DEBUG)

    ch = logging.StreamHandler()
    formatter = CustomFormatter()
    ch.setFormatter(formatter)

    if cmdargs.quiet:
        ch.setLevel(logging.CRITICAL)
    elif cmdargs.debug:
        ch.setLevel(logging.DEBUG)
    else:
        ch.setLevel(logging.INFO)

    logger.addHandler(ch)

    if 'func' not in cmdargs:
        parser.print_help()
        sys.exit(1)

    cmdargs.func(cmdargs)

if __name__ == '__main__':
    cmd()
