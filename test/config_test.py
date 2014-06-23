
import unittest
import os
import sys

from squeeze.app import Config

class TestConfig(unittest.TestCase):

   def setUp(self):
      testdir = os.path.dirname(os.path.abspath(__file__))
      self.conf = Config(testdir + "/data/sample_config.yml")

   def test_get_dict(self):
      self.assertEquals({"key3": "value2", "key4": "value3"}, self.conf.get("key2"))

   def test_get_string(self):
      self.assertEquals("value1", self.conf.get("key1"))

   def test_get_array(self):
      self.assertEquals(["value4", "value5", "value6"], self.conf.get("key5"))

   def test_get_nested(self):
      self.assertEquals("value7", self.conf.get("key6.key7.key8.key9"))

   def test_get_default(self):
      self.assertEquals("default", self.conf.get("key0", "default"))

   def test_returns_none_with_no_default(self):
      self.assertEquals(None, self.conf.get("key0"))
