Squeeze
=======

Squeeze is a python library to allow you to hook into your vcs changesets.

Installation
------------

Setup can be performed by running the setup.py file

```sh
git clone https://github.com/ryakad/squeeze
cd squeeze
python setup.py install
```


2. Create a git plugin file called git-squeeze and put it somewhere in your
shell search path. Make it executable and this can now be run as `git squeeze`
from inside a git repository.

3. Add the following content to git-squeeze

```python

from squeeze import *

# Define a function that will be run when git-squeeze detects an added file
# since the last run.
def on_file_add(delta, *files):
   print "Added file " + files[0]

squeeze = Squeeze()

# Add your custom function as a handler for when the file is added
squeeze.add_handler(on_file_add, squeeze.FILE_ADDED)

# run your squeeze
squeeze.run()

```

You can see from the above code that adding callbacks for file changes is
quite simple. Other changes that can be used are:

+ squeeze.FILE_ADDED    - set when a file is added
+ squeeze.FILE_DELETED  - set when a file is removed
+ squeeze.FILE_MODIFIED - set when a file is modified
+ squeeze.FILE_COPIED   - set when a file is copied from an existing file
+ squeeze.FILE_RENAMED  - set when a file is renamed


More Examples
-------------

Using the same function for different change types:

```python

def handle_multiple(delta, *files):
   if delta == FILE_ADDED:
      # handle addition
   elif delta == FILE_DELETED:
      # Handle file deletion

squeeze = squeeze.Squeeze()
squeeze.add_handler(handle_multiple, FILE_ADDED | FILE_DELETED)
squeeze.run()

```
