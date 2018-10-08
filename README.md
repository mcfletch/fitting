# Django Pipe-fitting Components

This is a simple module that allows for arbitrary graphs
in database of (small numbers of) records. It's intended to
allow you to create (sets of) processing graphs among any 
set of records.

Each Fitting record is tagged with an (arbitrary) type
integer, so each graph-type can be worked with independently.

```
from django.db import models
from fitting import models as fitting_models

class ProcessX(fitting_models.PipeElement, models.Model):
    """An element that is mixed"""


p = ProcessX.objects.create()
p.sources() # elements mapping into this
s.sinks() # elements mapped from this
s.pipe_to(target,clear=True,fitting_type=1)
s.pipe_from(target,clear=True,fitting_type=1)
s.ancestors(fitting_type=1)
s.descendants(fitting_type=1)
```

## Installation

Django application, use:

    setup.py install

(requires setuptools), then add to INSTALLED_APPLICATIONS

## Changes

* 1.0.6 -- eliminate deprecation warnings for Django 2.x
