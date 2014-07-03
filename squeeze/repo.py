#! /usr/bin/env python
#
# GitSqueeze
# Copyright (c) Ryan Kadwell <ryan@riaka.ca>
#
# Contains classes to generate diff data from repo
#
# Author: Ryan Kadwell <ryan@riaka.ca>
#

import re
import .core
from .util import Command

def get_repo(repo_type, path, **kwargs):
   """Return a repo of the given type initialised with kwargs

      This method is a factory constructor for creating different repository
      classes.

      Currently supported VCSs are Git and Mercurial.
   """
   repo_type = repo_type.lower()
   if repo_type == "git":
      return GitRepo(path, **kwargs)
   elif repo_type == "hg" or repo_type == "mercurial":
      return HgRepo(path, **kwargs)
   else:
      raise ValueError("Unsupported repo_type \"{0}\" provided".format(repo_type))

class BaseRepo(object):
   def __init__(self, path, **kwargs):
      self.base_path = path
      # different repo's might have different options so just treat them all
      # as keyword arguments.
      self.options = kwargs

   def get_option(self, option_name, default=None):
      if option_name in self.options:
         return self.options[option_name]
      else:
         return default

   def has_commit(self, identifier):
      return identifier in self.commit_list

# Our representation of a git repository
class GitRepo(BaseRepo):

   @property
   def commit_list(self):
      """Return an array of commits that are in the repo

         Only the commit identifier should be returned and should be in reverse
         order. The newest commit sha should be first in the list.
      """
      try:
         return self._commit_list
      except AttributeError:
         returncode, stdout, stder = Command.run(['git', 'rev-list', '--all'], cwd=self.base_path)
         if not returncode == 0:
            return None

         self._commit_list = stdout

         return self._commit_list

   def diff(self, a, b):
      """Returns diff data representing delta required to from commit a to b

         diff will return an array of tuples in the format (DELTA, [files])
         where delta is one of:

         squeeze.core.FILE_ADDED
         squeeze.core.FILE_DELETED
         squeeze.core.FILE_MODIFIED
         squeeze.core.FILE_COPIED
         squeeze.core.FILE_RENAMED
      """
      changes = []

      if a == b:
         # Nothing to do.
         pass
      elif not a:
         branch = "master" # TODO Use the current branch
         # Everything in repo is new since we dont have a starting point
         returncode, stdout, stderr = Command.run(
            ['git', 'ls-tree', '-r', branch, '--name-only'],
            cwd=self.base_path
         )

         if not returncode == 0:
            self.exit('Unable to list the git tree to file files in project')

         for line in stdout:
            changes.append((core.FILE_ADDED, [line]))
      else:
         if not b:
            b = "HEAD"

         diff = "{0}..{1}".format(a, b)
         returncode, stdout, stderr = Command.run(
            ['git', 'diff', '--name-status', '-C', diff],
            cwd=self.base_path
         )

         if not returncode == 0:
            raise Exception("Unable to find changed files")

         changes = self._parse_diff(stdout)

      return changes

   def _parse_diff(self, lines):
      changes = []
      for line in lines:
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
         return [(core.FILE_ADDED, files)]

      elif changetype == "M":
         return [(core.FILE_MODIFIED, files)]

      elif changetype == "D":
         return [(core.FILE_DELETED, files)]

      elif re.match(r'^R[0-9]+$', changetype):
         similarity = int(changetype.lstrip("R"))
         if similarity >= self.get_option('rename_similarity', 100):
            return [(core.FILE_RENAMED, files)]
         else:
            return [(core.FILE_DELETED, [files[0]]), (core.FILE_ADDED, [files[1]])]

      elif re.match(r'^C[0-9]+$', changetype):
         similarity = int(changetype.lstrip("C"))
         if similarity >= self.get_option('copy_similarity', 100):
            return [(core.FILE_COPIED, files)]
         else:
            return [(core.FILE_ADDED, [files[1]])]

# Our representation of a mercurial repository
class HgRepo(BaseRepo):

   @property
   def commit_list(self):
      """Return an array of commits that are in the repo

         Only the commit identifier should be returned and should be in reverse
         order. The newest commit sha should be first in the list.
      """
      try:
         return self._commit_list
      except AttributeError:
         returncode, stdout, stder = Command.run(['hg', 'log', '--template', '{node}\n'], cwd=self.base_path)
         if not returncode == 0:
            return None

         self._commit_list = stdout

         return self._commit_list

   def diff(self, a, b):
      changes = []

      if a == b:
         # Nothing to do.
         pass
      elif not a:
         # Treat everything as new
         returncode, stdout, stderr = Command.run(
            ["hg", "locate"],
            cwd=self.base_path
         )

         if not returncode == 0:
            raise Exception("Unable to find changed files")

         for line in stdout:
            changes.append((core.FILE_ADDED, [line]))
      else:
         if not b:
            b = "tip"

         diff = "{0}:{1}".format(a, b)
         returncode, stdout, stderr = Command.run(
            ["hg", "status", "-A", "--rev", diff]
         )

         if not returncode == 0:
            raise Exception("Unable to find changed files")

         diff = self._parse_diff(stdout)

         changes.append([(core.FILE_ADDED, x) for x in diff['ADDED']])
         changes.append([(core.FILE_DELETED, x) for x in diff['DELETED']])
         changes.append([(core.FILE_MODIFIED, x) for x in diff['MODIFIED']])
         changes.append([(core.FILE_RENAMED, x) for x in diff['RENAMED']])
         changes.append([(core.FILE_COPIED, x) for x in diff['COPIED']])

      return changes

   def _parse_diff(self, diff_lines):
      diff = {
         'ADDED':[], 'DELETED':[], 'MODIFIED':[], 'COPIED':[], 'RENAMED':[]
      }

      for line in diff_lines:
         changetype, path = line[0], line[2:]
         if changetype == "A" or changetype == "C": # added
            if changetype == "A":
               last_added = path
            diff['ADDED'].append([path])
         elif changetype == "M":
            diff['MODIFIED'].append([path])
         elif changetype == "R":
            # If this path is the first path in a copy then change the copy
            # to a rename
            match_copied = [ x for x in diff['COPIED'] if x[0] == path ]
            if match_copied:
               for files in match_copied:
                  diff['RENAMED'].append(files)
               diff['COPIED'] = [ x for x in diff['COPIED'] if x[0] != path]
            else:
               diff['DELETED'].append([path])

         elif changetype == " ": # origin of the previous file listed as A
            if last_added: # This should always be true
               diff['COPIED'].append([path, last_added])
               if [last_added] in diff['ADDED']:
                  diff['ADDED'].remove([last_added])

      return diff
