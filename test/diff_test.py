import unittest

from gitsqueeze import diff

class HgDiffTest(unittest.TestCase):

   def test_can_parse_diff(self):
      diffdata = [
         'A file1',
         'A file2',
         'R file3',
         'A file4',
         '  file5',
         'R file5',
         'A file6',
         '  file7',
         'C file8'
      ]

      d = diff.HgDiff("")
      result = d._parse_diff(diffdata)

      self.assertEquals(result, {
         'ADDED': [["file1"], ["file2"], ["file8"]],
         'DELETED': [["file3"]],
         'MODIFIED': [],
         'COPIED': [['file7', 'file6']],
         'RENAMED': [['file5', 'file4']]
      })

   def test_can_parse_empty_diff(self):
      diffdata = []
      d = diff.HgDiff("")
      result = d._parse_diff(diffdata)
      self.assertEquals({
         'ADDED': [],
         'DELETED': [],
         'MODIFIED': [],
         'COPIED': [],
         'RENAMED': []
      }, result)

   def test_can_detect_copied_files(self):
      diffdata = [
         'A file1',
         '  file2',
      ]

      d = diff.HgDiff("")
      result = d._parse_diff(diffdata)

      self.assertEquals(result, {
         'ADDED': [],
         'DELETED': [],
         'MODIFIED': [],
         'COPIED': [["file2", "file1"]],
         'RENAMED': []
      })

   def test_can_detect_renamed_files(self):
      diffdata = [
         'A file1',
         '  file2',
         'R file2'
      ]

      d = diff.HgDiff("")
      result = d._parse_diff(diffdata)

      self.assertEquals(result, {
         'ADDED': [],
         'DELETED': [],
         'MODIFIED': [],
         'COPIED': [],
         'RENAMED': [["file2", "file1"]]
      })
