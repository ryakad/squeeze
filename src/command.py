
import subprocess

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
