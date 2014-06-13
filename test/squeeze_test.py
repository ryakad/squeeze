
import unittest
import os
import sys

from gitsqueeze import *


class TestSqueeze(unittest.TestCase):

   def test_parse_diff_line(self):
      s = Squeeze()
      self.assertEqual(
         s.parse_diff_line("A\ttestfile"),
         ("A", ["testfile"])
      )

      self.assertEqual(
         s.parse_diff_line("C100\ttestfile\ttest"),
         ("C100", ["testfile", "test"])
      )
