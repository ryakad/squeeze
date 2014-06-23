#! /usr/bin/env python
#
# squeeze
# Copyright (c) Ryan Kadwell <ryan@riaka.ca>
#
# Script to process file changes on a scm repository as commits are made.
#
# Author: Ryan Kadwell <ryan@riaka.ca>
#

import os
import sys
import logbook
import psutil
import yaml

from repo import get_repo
from util import Command

class Squeeze(object):
   """Implementation of the squeeze library"""
   def __init__(self):
      """Initialize the Application Runner"""
      self.project_base_dir = self.get_base_dir()

      if self.project_base_dir == None:
         # We don't have a squeeze repo therefore can not do anything.
         # Just exit
         sys.stderr.write("Unable to find squeeze basedir\n")
         sys.exit(1)

      self.data_path = os.path.abspath(self.project_base_dir + "/.squeeze")

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

      self.repo = repo = get_repo(
         repo_type=self.config.get("repo", "git"),
         path=self.project_base_dir,
         rename_similarity=self.config.get("similarity.rename", 100),
         copy_similarity=self.config.get("similarity.copy", 100)
         )

      # Setup the runner
      self.runner = DiffRunner(self.repo)

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
      return os.path.abspath(path + "/..").replace('//','/')

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
         # TODO Allow users to set log file in config. File will need to be
         # writable by user running command. Check that and if not fall back
         # to this log with an error on stderr.

         handler = logbook.FileHandler(os.path.abspath(self.data_path + "/current.log"))
         handler.push_application()

         self._logger = logbook.Logger('Squeeze')
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

   def run(self):
      self.logger.debug('Starting Run')
      try:
         commits = self.repo.commit_list
         if commits == None:
            self.exit('Unable to find latest commit hash')

         if len(commits) == 0:
            self.exit('There are currently no commits in repo')

         latest_hash = commits[0]

         # make sure that we can even find the last commit in the tree.
         if self.last_run and self.last_run != latest_hash and self.last_run not in commits:
            msg = 'Commit "{0}" not in history'.format(self.last_run)
            self.logger.error(msg)
            self.exit(msg)

         self.logger.notice("Querying changes from {0} to {1}.".format(self.last_run, latest_hash))

         self.runner.run(self.last_run, latest_hash)

         self.last_run = latest_hash

         # Done processing so cleanup
         self._cleanup()

      except Exception, e:
         self.exit(str(e))

   def _cleanup(self):
      if not remove_pid_lock_file(self.lockfile):
         self.logger.error("Unable to remove lockfile")
         self.exit("Unable to remove lockfile. IF you are sure no other process is running you may remove the file {0} manually and try again".format(self.lockfile))

   def exit(self, message, exitcode=1):
      """Writes a message to stderror and exits"""
      self.logger.critical(message)
      sys.stderr.write('ERROR ' + message + "\n")
      self._cleanup()
      sys.exit(exitcode)

   def add_handler(self, function, delta):
      self.runner.add_handler(function, delta)


def create_pid_lock_file(filename):
   # A PID file exists we can check if we are able to remove it (i.e. the process
   # has ended but did not remove the lock file)
   if os.path.exists(filename) and not remove_pid_lock_file(filename):
      return False

   with open(filename, "w") as f:
      f.write(str(os.getpid()))

   return True

def remove_pid_lock_file(filename):
   with open(filename, "r") as f:
      pid = f.read().strip()

   # Check if the process is still running and only remove if it is not
   process = [p for p in psutil.get_process_list() if p.pid==pid]
   if not process:
      os.remove(filename)
      return True
   else:
      return False


class Config(object):
   """Squeeze config object"""
   def __init__(self, filename):
      if not os.path.exists(filename):
         raise ValueError("The file {0} does not exist".format(filename))
      elif not os.access(filename, os.R_OK):
         raise ValueError("The file {0} is not readable".format(filename))

      with open(filename) as f:
         self.config_data = yaml.load(f)

   def get(self, value_name, default=None):
      data = self.config_data
      for key in value_name.split("."):
         if key in data:
            data = data[key]
         else:
            return default

      return data
