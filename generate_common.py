#!/usr/bin/env python3
#                                                  -*- coding: utf-8 -*-
# A library to display spinorama charts
#
# Copyright (C) 2020 Pierre Aubert pierreaubert(at)yahoo(dot)fr
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import logging
import sys


def get_custom_logger(duplicate=False):
    custom = logging.getLogger("spinorama")
    fh = logging.FileHandler("debug_optim.log")
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    fh.setFormatter(formatter)
    custom.addHandler(fh)
    if duplicate is True:
        sh = logging.StreamHandler(sys.stdout)
        sh.setFormatter(formatter)
        custom.addHandler(sh)
    return custom


def args2level(args):
    level = logging.INFO
    if args["--log-level"] is not None:
        check_level = args["--log-level"]
        if check_level in ("INFO", "DEBUG", "WARNING", "ERROR"):
            if check_level == 'INFO':
                level = logging.INFO
            elif check_level == 'DEBUG':
                level = logging.DEBUG
            elif check_level == 'WARNING':
                level = logging.WARNING
            elif check_level == 'ERROR':
                level = logging.ERROR
    return level
