#! /usr/bin/env python
#
# GitSqueeze
# Copyright (c) Ryan Kadwell <ryan@riaka.ca>
#
# Contains classes to generate diff data from repo
#
# Author: Ryan Kadwell <ryan@riaka.ca>
#

import squeeze
import re
from util import Command


class GitDiff(object):
   """Find diff data for a git repository"""

   def __init__(self, path, rename_similarity=100, copy_similarity=100, branch="master"):
      self.base_path = path
      self.rename_similarity = rename_similarity
      self.copy_similarity = copy_similarity
      self.branch = branch

   def diff(self, a, b):
      """Returns diff data representing delta required to from commit a to b

         diff will return an array of tuples in the format (DELTA, [files])
         where delta is one of:

         squeeze.FILE_ADDED
         squeeze.FILE_DELETED
         squeeze.FILE_MODIFIED
         squeeze.FILE_COPIED
         squeeze.FILE_RENAMED
      """
      changes = []

      if a == b:
         # Nothing to do.
         pass

      elif not a:
         # Everything in repo is new since we dont have a starting point
         returncode, stdout, stderr = Command.run(
            ['git', 'ls-tree', '-r', self.branch, '--name-only'],
            cwd=self.base_path
         )

         if not returncode == 0:
            self.exit('Unable to list the git tree to file files in project')

         for line in stdout:
            changes.append((squeeze.FILE_ADDED, [line]))
      else:
         diff = "{0}..{1}".format(a, b)

         returncode, stdout, stderr = Command.run(
            ['git', 'diff', '--name-status', '-C', diff]
         )

         if not returncode == 0:
            raise Exception("Unable to find changed files")

         for line in stdout:
            changes = changes + self._parse_diff_line(line)

      return changes

   def _parse_diff_line(self, line):
      """Parse lines from git diff to the desired format

         Converts the lines returned from git diff into a tule contining the
         change type as the first parameter and an array of effected files as
         the second parameter.
      """
      # TODO This does not respect tabs in filenames. Tho rare and discouraged
      # it is allowed and should be handled properly.
      parts = re.split(r'\t+', line.strip())

      changetype = parts[0]
      files = parts[1:]

      if changetype == "A":
         return [(squeeze.FILE_ADDED, files)]

      elif changetype == "M":
         return [(squeeze.FILE_MODIFIED, files)]

      elif changetype == "D":
         return [(squeeze.FILE_MODIFIED, files)]

      elif re.match(r'^R[0-9]+$', changetype):
         similarity = int(changetype.lstrip("R"))
         if similarity >= self.rename_similarity:
            return [(squeeze.FILE_RENAMED, files)]
         else:
            return [(squeeze.FILE_DELETED, files[0]), (squeeze.FILE_ADDED, files[1])]

      elif re.match(r'^C[0-9]+$', changetype):
         similarity = int(changetype.lstrip("C"))
         if similarity >= self.copy_similarity:
            return [(squeeze.FILE_COPIED, files)]
         else:
            return [(squeeze.FILE_ADDED, files[1])]
