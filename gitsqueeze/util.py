#! /usr/bin/env python
#
# git-squeeze
# Copyright (c) Ryan Kadwell <ryan@riaka.ca>
#
# Script to process file changes on a git repository as commits are made.
#
# Author: Ryan Kadwell <ryan@riaka.ca>
#

import subprocess
import os
import psutil
import yaml


class Command(object):
   """Wrapper for subprocess.Popen"""

   @staticmethod
   def run(args, cwd="."):
      """Wrap subprocess.Popen command execution

         Runs a command using subprocess and return a tuple containing the
         return code, stdout, stderr.
      """
      proc = subprocess.Popen(
         args, stderr=subprocess.PIPE, stdout=subprocess.PIPE, cwd=cwd
      )

      proc.wait() # wait for command to finish before we carry on

      stdout = []
      for line in proc.stdout:
         stdout.append(line.rstrip('\n'))

      stderr = []
      for line in proc.stderr:
         stderr.append(line.rstrip('\n'))

      return proc.returncode, stdout, stderr


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
