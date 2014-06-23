#! /usr/bin/env python
#
# GitSqueeze
# Copyright (c) Ryan Kadwell <ryan@riaka.ca>
#
# Main init for gitsqueeze module
#
# Author: Ryan Kadwell <ryan@riaka.ca>
#

from app import Squeeze
from core import (
   FILE_ADDED,
   FILE_DELETED,
   FILE_MODIFIED,
   FILE_COPIED,
   FILE_RENAMED
   )

__all__ = [
   "Squeeze",
   "FILE_ADDED",
   "FILE_DELETED",
   "FILE_MODIFIED",
   "FILE_COPIED",
   "FILE_RENAMED"
   ]
