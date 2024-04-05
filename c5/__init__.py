# SPDX-License-Identifier: GPL-2.0-only
# Copyright (c) 2022 Nikita Travkin <nikita@trvn.ru>

import logging
import os
import subprocess
import difflib
import multiprocessing

import b4
import b4.ez
import b4.ty

logger = logging.getLogger('c5')
color = True

def git_find_base_commit():
    """Return the commit id before the first change to test"""
    series_start = b4.ez.get_series_start()
    return series_start

def git_get_commit_subject(commit):
    """Return the subject line of the commit"""
    _, out = b4.ty.git_get_commit_message(None, commit)
    return out.splitlines()[0]

def git_get_changed_files(commit):
    """Return a list of files changed by the commit"""
    gitargs = ["diff-tree", "--no-commit-id", "--name-only", commit, "-r"]
    lines = b4.git_get_command_lines(None, gitargs)
    return lines


def run_command(cmdargs, stdin=None, rundir=None):
    if rundir:
        logger.debug('Changing dir to %s', rundir)
        curdir = os.getcwd()
        os.chdir(rundir)
    else:
        curdir = None

    logger.debug('Running %s' % ' '.join(cmdargs))
    sp = subprocess.Popen(cmdargs, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    (output, error) = sp.communicate(input=stdin)
    if curdir:
        logger.debug('Changing back into %s', curdir)
        os.chdir(curdir)

    return sp.returncode, output, error


def linux_temp_builddir():
    """create the builddir if needed and return the path"""
    kernel_base = b4.git_get_toplevel()
    if kernel_base is None:
        raise RuntimeError()

    tempdir = kernel_base + "/.c5-out/"

    if not os.path.exists(tempdir):
        logger.debug('Creating %s', tempdir)
        os.makedirs(tempdir)

    return tempdir

def core_count():
    """Get amount of useful cores to compile with, leaving some to the user"""
    cnt = multiprocessing.cpu_count()
    if cnt > 4:
        return cnt - 2
    else:
        return cnt - 1

# FIXME: this assumes aarch64
def linux_make(makeargs, archenvs=["CROSS_COMPILE=aarch64-linux-gnu-", "ARCH=arm64"]):
    """Run make in the current kernel dir"""
    tempdir = linux_temp_builddir()
    cmdargs = ["make", f"-j{core_count()}", f"KBUILD_OUTPUT={tempdir}"] + archenvs + makeargs

    return run_command(cmdargs)

def linux_logfile(name):
    """Get a logfile path"""
    tempdir = linux_temp_builddir()
    return f"{tempdir}/log-{name}.txt"


def _fuzzy_cmp(newl, oldlines, fuzzy):
    maxr = 0
    for oldl in oldlines:
        ratio = difflib.SequenceMatcher(None, oldl, newl).ratio()
        maxr = max(maxr, ratio)

    if maxr < fuzzy:
        return newl

    return None

def get_new_lines(old, new, fuzzy=0.98):
    oldlines = set(old.splitlines(keepends=True))
    newlines = new.splitlines(keepends=True)

    if len(oldlines) == 0:
        return new

    tmp = []
    for newl in newlines:
        if newl not in oldlines:
            tmp.append(newl)

    with multiprocessing.Pool() as pool:
        matches = pool.starmap(_fuzzy_cmp, map(lambda x: (x, oldlines, fuzzy), tmp))

    ret = [ val for val in matches if val is not None ]

    seen = set()
    ret = [val for val in ret if not (val in seen or seen.add(val))]

    return "".join(ret)
