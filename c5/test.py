# SPDX-License-Identifier: GPL-2.0-only
# Copyright (c) 2022 Nikita Travkin <nikita@trvn.ru>

#pylint: disable=missing-function-docstring
#pylint: disable=missing-module-docstring

from contextlib import contextmanager

import b4

import c5
import c5.testcases

logger = c5.logger

def git_get_commits_after(base_commit):
    gitargs = ["log", "--format=\"%H\"", f"{base_commit}..HEAD"]
    lines = b4.git_get_command_lines(None, gitargs)
    lines.reverse()
    return [ line.replace("\"", "") for line in lines ]

def git_checkout(commit, detach=True):
    gitargs = ["checkout"]
    if detach:
        gitargs.append("--detach")

    gitargs.append(commit)
    b4.git_get_command_lines(None, gitargs)

@contextmanager
def git_detached_head(base_commit):
    try:
        git_checkout(base_commit)
        yield None
    finally:
        git_checkout("-", detach=False)

def git_cherry_pick(commit):
    gitargs = ["cherry-pick", commit]
    ecode, _ = b4.git_run_command(None, gitargs)
    if ecode:
        raise RuntimeError()

def apply_and_test(commit):
    testcases = []
    for testcase in c5.testcases.get_testcases():
        case = testcase(commit)
        if case.applies():
            logger.debug("Preparing testcase: %s", testcase.desc)
            case.prep()
            testcases.append(case)

    git_cherry_pick(commit)

    for case in testcases:
        logger.debug("Running testcase: %s", case.desc)
        case.run()


def main(_):
    base_commit = c5.git_find_base_commit()
    logger.debug("Base commit is '%s' %s", base_commit[:12], c5.git_get_commit_subject(base_commit))

    commits = git_get_commits_after(base_commit)
    if not commits:
        logger.info("Nothing to test")
    else:
        logger.info("Will test %d commits", len(commits))

    with git_detached_head(base_commit):
        for commit in commits:
            logger.info("Testing commit '%s' %s", commit[:12], c5.git_get_commit_subject(commit))
            apply_and_test(commit)

        logger.info("Done!")
