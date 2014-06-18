#! /usr/bin/env python
#
# GitSqueeze
# Copyright (c) Ryan Kadwell <ryan@riaka.ca>
#
# Tests for the gitsqeeze.repo classes
#
# Author: Ryan Kadwell <ryan@riaka.ca>
#

import unittest

from gitsqueeze import *
from gitsqueeze import repo

class HgRepoTest(unittest.TestCase):

   def test_parse_diff(self):
      diff_lines = [
         'A file1', # add file1 and file2
         'A file2',
         'R file3', # remove file3
         'A file4', # rename file5 -> file4
         '  file5',
         'R file5',
         'A file6', # copy file7 to file6
         '  file7',
         'C file8',  # add file8
         'M file9'   # modify file9
      ]

      d = repo.HgRepo("")
      result = d._parse_diff(diff_lines)

      self.assertEquals(result, {
         'ADDED': [["file1"], ["file2"], ["file8"]],
         'DELETED': [["file3"]],
         'MODIFIED': [["file9"]],
         'COPIED': [['file7', 'file6']],
         'RENAMED': [['file5', 'file4']]
      })

   def test_parse_empty_diff(self):
      diff_lines = []
      d = repo.HgRepo("")
      result = d._parse_diff(diff_lines)
      self.assertEquals({
         'ADDED': [],
         'DELETED': [],
         'MODIFIED': [],
         'COPIED': [],
         'RENAMED': []
      }, result)

   def test_detect_copied_files(self):
      diff_lines = [
         'A file1',
         '  file2',
      ]

      d = repo.HgRepo("")
      result = d._parse_diff(diff_lines)

      self.assertEquals(result, {
         'ADDED': [],
         'DELETED': [],
         'MODIFIED': [],
         'COPIED': [["file2", "file1"]],
         'RENAMED': []
      })

   def test_detect_renamed_files(self):
      diff_lines = [
         'A file1',
         '  file2',
         'R file2'
      ]

      d = repo.HgRepo("")
      result = d._parse_diff(diff_lines)

      self.assertEquals(result, {
         'ADDED': [],
         'DELETED': [],
         'MODIFIED': [],
         'COPIED': [],
         'RENAMED': [["file2", "file1"]]
      })

class GitRepoTest(unittest.TestCase):
   def test_parse_diff(self):
      diff_lines = [
         'A\tfile1',
         'A\tfile2',
         'D\tfile3',
         'M\tfile4',
         'R100\tfile5\tfile6',
         'C100\tfile7\tfile8'
      ]

      d = repo.GitRepo("")
      result = d._parse_diff(diff_lines)

      self.assertEquals(result, [
         (FILE_ADDED, ["file1"]),
         (FILE_ADDED, ["file2"]),
         (FILE_DELETED, ["file3"]),
         (FILE_MODIFIED, ["file4"]),
         (FILE_RENAMED, ["file5", "file6"]),
         (FILE_COPIED, ["file7", "file8"])
      ])

   def test_detect_renamed_files(self):
      diff_lines = [
         "R100\tfile1\tfile2"
      ]

      d = repo.GitRepo("")
      result = d._parse_diff(diff_lines)

      self.assertEquals(result, [
         (FILE_RENAMED, ["file1", "file2"])
      ])

   def test_respect_rename_similarity(self):
      diff_lines = [
         "R090\tfile1\tfile2"
      ]

      d = repo.GitRepo("")
      result = d._parse_diff(diff_lines)

      self.assertEquals(result, [
         (FILE_DELETED, ["file1"]),
         (FILE_ADDED, ["file2"])
      ])

   def test_can_lower_required_rename_similarity(self):
      diff_lines = [
         "R090\tfile1\tfile2"
      ]

      d = repo.GitRepo("", rename_similarity=80)
      result = d._parse_diff(diff_lines)

      self.assertEquals(result, [
         (FILE_RENAMED, ["file1", "file2"])
      ])

   def test_detect_copied_files(self):
      diff_lines = [
         "C100\tfile1\tfile2"
      ]

      d = repo.GitRepo("")
      result = d._parse_diff(diff_lines)

      self.assertEquals(result, [
         (FILE_COPIED, ["file1", "file2"])
      ])

   def test_respect_copy_similarity(self):
      diff_lines = [
         "C090\tfile1\tfile2"
      ]

      d = repo.GitRepo("")
      result = d._parse_diff(diff_lines)

      self.assertEquals(result, [
         (FILE_ADDED, ["file2"])
      ])

   def test_can_lower_required_copy_similarity(self):
      diff_lines = [
         "C090\tfile1\tfile2"
      ]

      d = repo.GitRepo("", copy_similarity=80)
      result = d._parse_diff(diff_lines)

      self.assertEquals(result, [
         (FILE_COPIED, ["file1", "file2"])
      ])
