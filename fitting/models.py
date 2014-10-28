from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic

class Fitting(models.Model):
    """A directional fitting in a pipeline
    
    A pipeline is just N connections between elements
    The connections (fittings) are setup by (external) business logic.
    There are N possible pipe namespaces, where each namespace creates
    a unique source:target mapping.
    
    Note: it is assumed that pipes are small, and that there are a 
    very limited number of them, so it is often reasonable to load 
    the whole pipe-space into memory to optimize operations.
    """
    class Meta:
        unique_together = [
            ('fitting_type','source_id','source_type', 'sink_id', 'sink_type'), 
        ]
    DEFAULT_PIPE_TYPE = 1
    fitting_type = models.IntegerField(
        verbose_name='Pipe Type', 
        default = DEFAULT_PIPE_TYPE,
        db_index=True,
    )
    source_type = models.ForeignKey(
        ContentType,
        null=False,blank=False,
        db_index=True,
        related_name="fitting_source_types"
    )
    source_id = models.PositiveIntegerField(
        null=False,blank=False,
        db_index=True,
    )
    source = generic.GenericForeignKey(
        'source_type', 'source_id', 
    )
    sink_type = models.ForeignKey(
        ContentType,
        null=False,blank=False,
        db_index=True,
        related_name="fitting_sink_types"
    )
    sink_id = models.PositiveIntegerField(
        null=False,blank=False,
        db_index=True,
    )
    sink = generic.GenericForeignKey(
        'sink_type', 'sink_id', 
    )
    @classmethod
    def sources(cls, instance,  pipe_type=None):
        """Retrieve all currently fitted sources"""
        return cls.objects.filter(
            sink=instance,
            fitting_type=pipe_type or cls.DEFAULT_PIPE_TYPE 
        )
    @classmethod
    def sinks(cls, instance, pipe_type=None):
        """Retrieve all current fitted sinks"""
        return cls.objects.filter(
            source=instance, 
            fitting_type=pipe_type or cls.DEFAULT_PIPE_TYPE 
        )
    @classmethod 
    def mapping(cls, pipe_type=None):
        """Get an in-memory source:[sinks] mapping"""
        result = {}
        for record in cls.filter(pipe_type=pipe_type or cls.DEFAULT_PIPE_TYPE):
            result.setdefault(record.source, []).append(record.sink)
        return result

class PipeElement(object):
    """Mix-in providing pipe-fitting manipulations
    
    A DEFAULT_PIPE_TYPE is defined, this is the pipe type 
    that will be assumed for these APIs, cases where there 
    is really just one type of pipe can thus ignore the 
    pipe_type arguments entirely.
    """
    DEFAULT_PIPE_TYPE = Fitting.DEFAULT_PIPE_TYPE
    def sources(self, pipe_type=None):
        """Retrieve all currently fitted sources"""
        return Fitting.sources(self, pipe_type=pipe_type or self.DEFAULT_PIPE_TYPE)
    def sinks(self, pipe_type=None):
        """Retrieve all current fitted sinks"""
        return Fitting.sinks(self, pipe_type=pipe_type or self.DEFAULT_PIPE_TYPE)
    def detach(self, pipe_type=None):
        self.sources(pipe_type=pipe_type).delete()
        self.sinks(pipe_type=pipe_type).delete()
        return self
    def pipe_into(self, other, clear=True, pipe_type=None):
        """Pipe this element into another
        
        clear -- if True, delete all current outgoing pipes
        """
        if clear:
            self.sinks(pipe_type=pipe_type).delete()
        return Fitting.objects.create(
            source = self, 
            sink = other, 
            pipe_type=pipe_type or self.DEFAULT_PIPE_TYPE, 
        )
    def pipe_from(self, other, clear=True, pipe_type=None):
        """Pipe this element from another element
        
        clear -- if True, delete all current incoming pipes
        """
        if clear:
            self.sources(pipe_type=pipe_type).delete()
        return other.pipe_into(self, clear=False, pipe_type=pipe_type)

from django.db.models.signals import pre_delete
from django.dispatch.dispatcher import receiver
@receiver(pre_delete)
def unlink_fittings_on_deletion(sender, **named):
    """Unlink any fitting registered for a to-delete sender
    
    NOTE: this runs on *every* deletion of *any* record, this 
    is a bit of a huge club to solve a minor issue, but it should
    prevent dangling references and doesn't affect my use cases.
    """
    if not isinstance(sender, Fitting):
        Fitting.objects.filter(source=sender).delete()
        Fitting.objects.filter(sink=sender).delete()
