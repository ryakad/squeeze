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
import logbook

from util import Command, Config, create_pid_lock_file, remove_pid_lock_file
from diff import GitDiff

# Flags for change types
FILE_ADDED    = 0b00001 # 1
FILE_DELETED  = 0b00010 # 2
FILE_MODIFIED = 0b00100 # 4
FILE_COPIED   = 0b01000 # 8
FILE_RENAMED  = 0b10000 # 16


class Squeeze(object):

   def __init__(self):
      """Initialize the Application Runner"""
      self.project_base_dir = self.get_base_dir()

      # Make sure that the git subdir exists!
      self.data_path = os.path.abspath(self.project_base_dir + "/.squeeze")
      if not os.path.exists(self.data_path):
         os.makedirs(self.data_path)

      self.logger.debug('Initializing')
      # Check & initialize lockfile
      self.lockfile = os.path.abspath(self.data_path + '/.lock')
      if not create_pid_lock_file(self.lockfile):
         self.logger.critical("Unable to create lockfile for process")
         self.exit("Unable to create lockfile for process")

      # Initialize the handlers container
      self.handlers = {}

      # These files do not neccesarily exist at this point.
      self.latest_run = os.path.abspath(self.data_path + "/latest")

      # Load the config file. Creating it if it does not already exist.
      config_path = self.data_path + "/config.yml"
      if not os.path.exists(config_path):
         open(config_path, 'a').close()

      self.config = Config(config_path)

   def get_base_dir(self):
      startpath = os.getcwd()
      if self._is_base_dir(startpath):
         return startpath

      prev_checkpath = startpath
      checkpath = self._parent_path(startpath)

      while checkpath != prev_checkpath:
         if self._is_base_dir(checkpath):
            return checkpath

         prev_checkpath = checkpath
         checkpath = self._parent_path(checkpath)

      return None

   def _parent_path(self, path):
      return os.path.abspath(path + "/..")

   def _is_base_dir(self, path):
      for filename in os.listdir(path):
         if filename == ".squeeze" and os.path.isdir(os.path.abspath(path + "/.squeeze")):
            return True

      return False

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
      self.logger.debug('Starting Run')
      try:
         # Find what commit we are processing up to.
         returncode, stdout, stder = Command.run(['git', 'rev-list', '--all'])
         if not returncode == 0:
            self.exit('Unable to find latest commit hash')

         revlist = stdout

         if len(stdout) == 0:
            self.exit('There are currently no commits in repo')

         latest_hash = revlist[0]

         # make sure that we can even find the last commit in the tree.
         if self.last_run and self.last_run != latest_hash and self.last_run not in revlist:
            msg = 'Commit "{0}" not in rev-list'.format(self.last_run)
            self.logger.error(msg)
            self.exit(msg)

         self.logger.notice("Querying changes from {0} to {1}.".format(self.last_run, latest_hash))
         diff = GitDiff(
            path=self.project_base_dir,
            rename_similarity=self.config.get("similarity.rename", 100),
            copy_similarity=self.config.get("similarity.copy", 100)
            )
         changes = diff.diff(self.last_run, latest_hash)

         for changetype, files in changes:
            for function in self.get_handlers_for(changetype):
               function(changetype, *files)

         self.last_run = latest_hash

         # Done processing so cleanup
         self._cleanup()

      except Exception, e:
         self.exit(str(e))

   def _cleanup(self):
      if not remove_pid_lock_file(self.lockfile):
         self.logger.error("Unable to remove lockfile")
         self.exit("Unable to remove lockfile. IF you are sure no other process is running you may remove the file {0} manually and try again".format(self.lockfile))

   def get_handlers_for(self, delta):
      funcs = []
      for index in [x for x in self.handlers if x & delta]:
         funcs = funcs + self.handlers[index]

      return funcs

   def exit(self, message, exitcode=1):
      """Writes a message to stderror and exits"""
      self.logger.critical(message)
      sys.stderr.write('ERROR ' + message + "\n")
      self._cleanup()
      sys.exit(exitcode)

   def add_handler(self, function, delta):
      if delta not in self.handlers:
         self.handlers[delta] = [function]
      else:
         self.handlers[delta].append(function)
