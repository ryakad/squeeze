Squeeze
=======

[![Build Status](https://secure.travis-ci.org/ryakad/squeeze.png)](http://travis-ci.org/ryakad/squeeze)

Squeeze is a python library that allows you to hook into your VCS change sets
performing actions on the different file changes. The currently supported
VCSs are git and mercurial.


Installation
------------

Setup can be performed by running the setup.py file

```sh
git clone https://github.com/ryakad/squeeze
cd squeeze
python setup.py install
```

Once you have installed the library and are ready use squeeze with an
existing repo you will need to run the `squeeze` command in the base
directory of the repo to setup the required folders and config files. You
may also want to set your VCS to ignore the .squeeze directory.


How it works
------------

Squeeze is used to run a function against each diff in a change set depending
on the type of change. By default squeeze will keep track of the commit
identifier that it stopped at and will start at that commit next time. This
way each commit in the repo will be processed sequentially as changes are
committed. If you do not want this sequential style you can make use of the
core classes and customize squeeze to do what you need.


### Handling change sets

The different changes that squeeze will detect are:

```python
squeeze.FILE_ADDED    # set when a file is added
squeeze.FILE_DELETED  # set when a file is removed
squeeze.FILE_MODIFIED # set when a file is modified
squeeze.FILE_COPIED   # set when a file is copied from an existing file
squeeze.FILE_RENAMED  # set when a file is renamed
```

Each user function should be defined as:

```python
def function_name(change_type, *files):
   # handle changed file here
```

The change_type will be a constant representing the change type that the
file(s) has undergone. This makes it possible to have a function that
handles multiple change types like in the example below.

```python
def file_added(change_type, *files):
   if change_type == squeeze.FILE_ADDED:
      # Handle file addition.
      # Path to file will be stored at files[0]
      file = files[0]
   elif change_type == squeeze.FILE_COPIED:
      # Handle file copy
      # For copies and renames files[0] is the origin and files[1] is the
      # destination
      file = files[1]
   else:
      raise ArgumentError('Invalid change_type for file_added()')

   # TODO process file as being added
   pass
```

Once you have defined functions to be run for changes you will need to tell
the application what changes you want that function called on. To do this
you use the add_handler(func, type) method. You can specify multiple change types using the binry `|` operator.

```python
s = squeeze.Squeeze()

function handle_rename_copy(type, *files):
   print "File {0} based off of file {1}".format(files[1], files[0])

s.add_handler(handle_rename_copy, squeeze.FILE_RENAMED | squeeze.FILE_COPIED)
```

To run the diff you just use the `run()` method.


### Sample Application

Here is a simple git plugin that just prints all the files that were added
since the last scan.

```python
#! /usr/bin/env python

# import the squeeze library
import squeeze

# Create a function that will handle file additions
def handle_add(delta, *files):
   if delta == squeeze.FILE_ADDED:
      print "ADDED " + files[0]
   elif delta == squeese.FILE_COPIED:
      print "ADDED " + files[1]

s = squeeze.Squeeze()

# Function will be called when a file addition is detected
s.add_handler(handle_add, squeeze.FILE_ADDED | squeeze.FILE_COPIED)

s.run()

```

For more samples you can look in the `examples` folder in this repo.

If you find any bugs or just want a new feature submit an issue on github -
or even better, a pull request.
