#! /usr/bin/env python
#
# git-squeeze
# Copyright (c) Ryan Kadwell <ryan@riaka.ca>
#
# Script to process file changes on a git repository as commits are made.
#
# Author: Ryan Kadwell <ryan@riaka.ca>

import os
import sys
import re
import logbook

from util import Command, createPIDLockFile, removePIDLockFile


# Flags for change types
FILE_ADDED = 1
FILE_DELETED = 2
FILE_MODIFIED = 4
FILE_COPIED = 8
FILE_RENAMED = 16


class Squeeze(object):

   def __init__(self):
      """Initialize the Application Runner"""
      # Make sure that the git subdir exists!
      self.data_path = os.path.abspath(self.git_base_dir + "/squeeze")
      if not os.path.exists(self.data_path):
         os.makedirs(self.data_path)

      # Check & initialize lockfile
      self.lockfile = os.path.abspath(self.data_path + '/.lock')
      if not createPIDLockFile(self.lockfile):
         self.logger.critical("Unable to create lockfile for process")
         self.exit("Unable to create lockfile for process")

      # Initialize the handlers container
      self.handlers = {}

      # Get the base path for the project. We will run all commands from here.
      self.project_base_dir = os.path.abspath(self.git_base_dir + "/..")

      # These files do not neccesarily exist at this point.
      self.latest_run = os.path.abspath(self.data_path + "/latest")

      self.remote = self.get_config('squeeze.remote')
      self.branch = self.get_config('squeeze.branch', 'master')

      self.logger.info(' =========== Starting Squeeze ===========')

   def get_config(self, value, default=None):
      returncode, stdout, stderr = Command.run(['git', 'config', value])
      if not returncode == 0:
         return default

      return ''.join(stdout).strip()

   @property
   def logger(self):
      try:
         return self._logger
      except AttributeError:
         # TODO Allow users to set log file in config. Will need to be
         # writable by user running command. Check that and if not fall back
         # to this log with an error on stderr.

         handler = logbook.FileHandler(os.path.abspath(self.data_path + "/current.log"))
         handler.push_application()

         self._logger = logbook.Logger('GitSqueeze')
         return self._logger

   @property
   def git_base_dir(self):
      try:
         return self._git_base_dir
      except AttributeError:
         returncode, stdout, stderr = Command.run(['git', 'rev-parse', '--git-dir'])

         if not returncode == 0:
            self.exit('unable to determin root git directory for path "{0}"'.format(os.getcwd()))

         stdout = ''.join(stdout).strip()

         self._git_base_dir = os.path.abspath(stdout).strip()

         # We need a valid git dir to proceed so check this now
         if not os.path.isdir(self.git_base_dir):
            self.exit('git root directory "{0}" does not exist'.format(self.git_base_dir))

         return self._git_base_dir

   @property
   def last_run(self):
      try:
         return self._last_run_hash
      except AttributeError:
         if not os.path.exists(self.latest_run):
            self.logger.warn('Unable to determin last run. Treating all files as new!')
            self._last_run_hash = None
         else:
            with open(self.latest_run, "r") as f:
               self._last_run_hash = f.read().strip()

         return self._last_run_hash

   @last_run.setter
   def last_run(self, value):
      if not os.path.exists(os.path.dirname(self.latest_run)):
         os.makedirs(os.path.dirname(self.latest_run))

      with open(self.latest_run, "w") as f:
         f.write(value)
         # f.truncate()

   def parse(self):
      try:
         # Make sure that we are on the proper branch to process.
         returncode, stdout, stderr = Command.run(['git', 'checkout', self.branch])
         if not returncode == 0:
            self.exit('Unable to checkout the master branch')

         # If we are taking changes to process from a remote check for them now.
         if self.remote:
            returncode, stdout, stderr = Command.run(['git', 'pull', self.remote, self.branch])
            if not returncode == 0:
               self.exit('Unable to fetch remote changes', 1)

         # Find what commit we are processing up to.
         returncode, stdout, stder = Command.run(['git', 'rev-list', '--all'])
         if not returncode == 0:
            self.exit('Unable to find latest commit hash')

         revlist = stdout

         if len(stdout) == 0:
            self.exit('There are currently no commits in repo')

         latest_hash = revlist[0]

         if latest_hash == self.last_run:
            self.logger.notice('Nothing to do.')
            self._cleanup()
            sys.exit(0)
         elif not self.last_run:
            # need to handle all files under revision as additions
            returncode, stdout, stderr = Command.run(
               ['git', 'ls-tree', '-r', self.branch, '--name-only'],
               cwd=self.project_base_dir
            )

            if not returncode == 0:
               self.exit('Unable to list the git tree to file files in project')

            for line in stdout:
               self.logger.notice('ADDED {0}'.format(line));
               for function in self.get_handlers_for(FILE_ADDED):
                  function(FILE_ADDED, line)

         elif self.last_run not in revlist:
            msg = 'Commit "{0}" not in rev-list'.format(self.last_run)
            self.logger.error(msg)
            self.exit(msg)

         else:
            # process files changed between commits
            diff = "{0}..{1}".format(self.last_run, latest_hash)

            self.logger.notice("Processing changes from {0} to {1}.".format(self.last_run, latest_hash))

            returncode, stdout, stderr = Command.run(
               ['git', 'diff', '--name-status', '-C', diff]
            )

            if not returncode == 0:
               self.exit('Unable to find changed files')

            for line in stdout:
               self._process_diff(line)

         self.last_run = latest_hash

         # Done processing so cleanup
         self._cleanup()

      except Exception, e:
         self.exit(str(e))

   def _cleanup(self):
      if not removePIDLockFile(self.lockfile):
         self.logger.error("Unable to remove lockfile")
         self.exit("Unable to remove lockfile. IF you are sure no other process is running you may remove the file {0} manually and try again".format(self.lockfile))

   def _process_diff(self, line):
      self.logger.debug('Called _process_diff for line: {0}'.format(line))
      changetype, files = self.parse_diff_line(line)

      if changetype == "A":
         self.logger.notice('ADDED {0}'.format(files[0]))
         for function in self.get_handlers_for(FILE_ADDED):
            function(FILE_ADDED, files[0])

      elif changetype == "M":
         self.logger.notice('MODIFIED {0}'.format(files[0]))
         for function in self.get_handlers_for(FILE_MODIFIED):
            function(FILE_MODIFIED, files[0])

      elif changetype == "D":
         self.logger.notice('DELETED {0}'.format(files[0]))
         for function in self.get_handlers_for(FILE_DELETED):
            function(FILE_DELETED, files[0])

      elif re.match(r'^R[0-9]+$', changetype):
         # We will check the similarity of the renamed file and if it is
         # less than deplou.rename-similarity we will use count it as an
         # addition and removal. Handling the removals first.
         similarity = int(changetype.lstrip("R"))
         if not similarity == self.get_config('squeeze.rename-similarity', 100):
            self.logger.notice('RENAMED {0} -> {1}'.format(files[0], files[1]))
            for function in self.get_handlers_for(FILE_RENAMED):
               function(FILE_RENAMED, files[0], files[1])
         else:
            self.logger.notice('DELETED {0}'.format(files[0]))
            self.logger.notice('ADDED {0}'.format(files[0]))
            for function in self.get_handlers_for(FILE_DELETED):
               function(FILE_DELETED, files[0])
            for function in self.get_handlers_for(FILE_ADDED):
               function(FILE_ADDED, files[0])

      elif re.match(r'^C[0-9]+$', changetype):
         # We handle this in a similar method to the rename. If the
         # similarity is less than squeeze.copy-similarity we will count
         # it as an addition.
         similarity = int(changetype.lstrip("C"))
         if similarity == self.get_config('squeeze.copy-similarity', 100):
            self.logger.notice('COPIED {0} -> {1}'.format(files[0], files[1]))
            for function in self.get_handlers_for(FILE_COPIED):
               function(FILE_COPIED, files[0], files[1])
         else:
            self.logger.notice('ADDED {0}'.format(files[0]))
            for function in self.get_handlers_for(FILE_ADDED):
               function(FILE_ADDED, files[1])

      else:
         self.exit("Unhandled change type " + changetype)

   def get_handlers_for(self, delta):
      funcs = []
      for index in [x for x in self.handlers if x & delta]:
         funcs = funcs + self.handlers[index]

      return funcs

   def parse_diff_line(self, line):
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

      return changetype, files

   def exit(self, message, exitcode=1):
      """Writes a message to stderror"""
      self.logger.critical(message)
      sys.stderr.write('ERROR ' + message + "\n")
      self._cleanup()
      sys.exit(exitcode)

   def add_handler(self, function, delta):
      if delta not in self.handlers:
         self.handlers[delta] = []

      self.handlers[delta].append(function)
