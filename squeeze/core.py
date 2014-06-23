#! /usr/bin/env python
#
# GitSqueeze
# Copyright (c) Ryan Kadwell <ryan@riaka.ca>
#
# Module for core squeeze classes
#
# Author: Ryan Kadwell <ryan@riaka.ca>
#

# Binary flags for delta types
FILE_ADDED    = 0b00001 # 1
FILE_DELETED  = 0b00010 # 2
FILE_MODIFIED = 0b00100 # 4
FILE_COPIED   = 0b01000 # 8
FILE_RENAMED  = 0b10000 # 16

class DiffRunner(object):
   """Process a VCS changset calling callbacks for each"""
   def __init__(self, repo):
      """Initialize the DiffRunner"""
      self.handlers = {}
      self.repo = repo

   def run(self, a, b):
      """Calls handler for each change between commits a and b"""
      if a and not self.repo.has_commit(a):
         raise ValueError('Repository does not have a commit identified by "{0}"'.format(a))
      elif b and not self.repo.has_commit(b):
         raise ValueError('Repository does not have a commit identified by "{0}"'.format(b))

      changes = self.repo.diff(a, b)

      for changetype, files in changes:
         for function in self.get_handlers_for(changetype):
            function(changetype, *files)

   def add_handler(self, function, delta):
      """Add a function to the list of handlers

         Available handler deltas are:
         squeeze.FILE_ADDED
         squeeze.FILE_DELETED
         squeeze.FILE_MODIFIED
         squeeze.FILE_COPIED
         squeeze.FILE_RENAMED

         The handler function should take as parameters a delta parameter for
         the type of change and a list of positional parameters representing
         the effected files.
      """
      if delta not in self.handlers:
         self.handlers[delta] = [function]
      else:
         self.handlers[delta].append(function)

   def get_handlers_for(self, delta):
      funcs = []
      for index in [x for x in self.handlers if x & delta]:
         funcs = funcs + self.handlers[index]

      return funcs
