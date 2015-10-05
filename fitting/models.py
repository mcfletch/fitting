from django.db import models, transaction
from django.contrib.contenttypes.models import ContentType
try:
    from django.contrib.contenttypes import fields as generic 
except ImportError:
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
    DEFAULT_FITTING_TYPE = 1
    fitting_type = models.IntegerField(
        verbose_name='Pipe Type', 
        default = DEFAULT_FITTING_TYPE,
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
    def sources(cls, instance,  fitting_type=None):
        """Retrieve fittings for all currently fitted sources"""
        ct = ContentType.objects.get_for_model(instance)
        return cls.objects.filter(
            sink_type=ct,
            sink_id = instance.pk, 
            fitting_type=fitting_type or cls.DEFAULT_FITTING_TYPE 
        ).order_by('source_type__id', 'source_id')
    @classmethod
    def sinks(cls, instance, fitting_type=None):
        """Retrieve fittings for all current fitted sinks"""
        ct = ContentType.objects.get_for_model(instance)
        return cls.objects.filter(
            source_type=ct,
            source_id = instance.pk, 
            fitting_type=fitting_type or cls.DEFAULT_FITTING_TYPE 
        ).order_by('sink_type__id', 'sink_id' )
    @classmethod 
    def mapping(cls, fitting_type=None):
        """Get an in-memory source:[sinks] mapping"""
        result = {}
        for record in cls.filter(fitting_type=fitting_type or cls.DEFAULT_FITTING_TYPE):
            result.setdefault(record.source, []).append(record.sink)
        return result

class PipeElement(object):
    """Mix-in providing pipe-fitting manipulations
    
    A DEFAULT_FITTING_TYPE is defined, this is the pipe type 
    that will be assumed for these APIs, cases where there 
    is really just one type of pipe can thus ignore the 
    fitting_type arguments entirely.
    """
    DEFAULT_FITTING_TYPE = Fitting.DEFAULT_FITTING_TYPE
    def _sources(self, fitting_type=None):
        return Fitting.sources(self, fitting_type=fitting_type or self.DEFAULT_FITTING_TYPE)
    def sources(self, fitting_type=None):
        """Retrieve all currently fitted sources (the actual objects)"""
        return [f.source for f in self._sources(fitting_type)]
    def _sinks(self, fitting_type=None):
        return Fitting.sinks(self, fitting_type=fitting_type or self.DEFAULT_FITTING_TYPE)
    def sinks(self, fitting_type=None):
        """Retrieve all current fitted sinks (the actual objects)"""
        return [f.sink for f in self._sinks(fitting_type)]
    def detach_sources(self, fitting_type=None):
        self._sources(fitting_type=fitting_type).delete()
    def detach_sinks(self, fitting_type=None):
        self._sinks(fitting_type=fitting_type).delete()
    def detach(self, fitting_type=None):
        self.detach_sources(fitting_type=fitting_type)
        self.detach_sinks(fitting_type=fitting_type)
        return self
    
    def pipe_to(self, other, clear=True, fitting_type=None):
        """Pipe this element into another
        
        clear -- if True, delete all current outgoing pipes
        """
        if clear:
            self._sinks(fitting_type=fitting_type).delete()
        return Fitting.objects.create(
            source = self, 
            sink = other, 
            fitting_type=fitting_type or self.DEFAULT_FITTING_TYPE, 
        )
    # alias
    pipe_into = pipe_to
    def pipe_from(self, other, clear=True, fitting_type=None):
        """Pipe this element from another element
        
        clear -- if True, delete all current incoming pipes
        """
        if clear:
            self._sources(fitting_type=fitting_type).delete()
        return other.pipe_to(self, clear=False, fitting_type=fitting_type)
    @classmethod
    def no_sources(cls, fitting_type=None):
        # find all instances of cls where there is no mapping to this 
        # instance...
        ct = ContentType.objects.get_for_model(cls)
        maps = Fitting.objects.filter(sink_type=ct).filter(
            fitting_type=fitting_type or cls.DEFAULT_FITTING_TYPE
        ).all()
        ids = [f.target_id for f in maps]
        return cls.objects.exclude(id__in=ids)

from django.db.models.signals import pre_delete
from django.dispatch.dispatcher import receiver
@receiver(pre_delete)
def unlink_fittings_on_deletion(sender, instance=None,  **named):
    """Unlink any fitting registered for a to-delete sender
    
    NOTE: this runs on *every* deletion of *any* record, this 
    is a bit of a huge club to solve a minor issue, but it should
    prevent dangling references and doesn't affect my use cases.
    """
    if not isinstance(instance, Fitting) and isinstance(instance,models.Model):
        try:
            ct = ContentType.objects.get_for_model(sender)
        except transaction.TransactionManagementError:
            # migration where get_for_model fails due to lack of transactionality
            return
        try:
            int(instance.pk)
        except ValueError:
            # obviously not compatible, so skip it...
            return 
        Fitting.objects.filter(source_type=ct, source_id=instance.pk).delete()
        Fitting.objects.filter(sink_type=ct, sink_id =instance.pk).delete()
