#!/usr/bin/env bash
#
# Run c5 from a git checkout.
#

REAL_SCRIPT=$(realpath -e ${BASH_SOURCE[0]})
SCRIPT_TOP="${SCRIPT_TOP:-$(dirname ${REAL_SCRIPT})}"

PYTHONPATH="${SCRIPT_TOP}" \
	exec python3 "${SCRIPT_TOP}/c5/command.py" "${@}"
