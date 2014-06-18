Git Squeeze
===========

Git Squeeze is a python library to allow you to hook into your git changesets.

Getting setup is easy.

1. Clone this repo and run the setup.py file `python setup.py install`

2. Create a git plugin file called git-squeeze and put it somewhere in your
shell search path. Make it executable and this can now be run as `git squeeze`
from inside a git repository.

3. Add the following content to git-squeeze

```python

import gitsqueeze

# Define a function that will be run when git-squeeze detects an added file
# since the last run.
def on_file_add(delta, *files):
   print "Added file " + files[0]

squeeze = gitsqueeze.Squeeze()

# Add your custom function as a handler for when the file is added
squeeze.add_handler(on_file_add, gitsqueeze.FILE_ADDED)

# run your squeeze
squeeze.run()

```

You can see from the above code that adding callbacks for file changes is
quite simple. Other changes that can be used are:

+ gitsqueeze.FILE_ADDED    - set when a file is added
+ gitsqueeze.FILE_DELETED  - set when a file is removed
+ gitsqueeze.FILE_MODIFIED - set when a file is modified
+ gitsqueeze.FILE_COPIED   - set when a file is copied from an existing file
+ gitsqueeze.FILE_RENAMED  - set when a file is renamed


More Examples
-------------

Using the same function for different change types:

```python

def handle_multiple(delta, *files):
   if delta == gitsqueeze.FILE_ADDED:
      # handle addition
   elif delta == gitsqueeze.FILE_DELETED:
      # Handle file deletion

squeeze = gitsqueeze.GitSqueeze()
squeeze.add_handler(handle_multiple, gitsqueeze.FILE_ADDED | gitsqueeze.FILE_DELETED)
squeeze.run()

```
