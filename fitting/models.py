from django.db import models, transaction
from django.contrib.contenttypes.models import ContentType
import logging, contextlib, functools
log = logging.getLogger(__name__)
try:
    from django.contrib.contenttypes import fields as generic, models as ct_models
except ImportError:
    from django.contrib.contenttypes import generic, models as ct_models

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
        related_name="fitting_source_types",
        on_delete=models.CASCADE,
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
        null=False,
        blank=False,
        db_index=True,
        related_name="fitting_sink_types",
        on_delete=models.CASCADE,
    )
    sink_id = models.PositiveIntegerField(
        null=False,blank=False,
        db_index=True,
    )
    sink = generic.GenericForeignKey(
        'sink_type', 'sink_id', 
    )
    def __json__(self):
        return {
            'pk':self.pk, 
            'type': self.__class__.__name__, 
            'fitting_type':self.fitting_type, 
            'source': {
                'app': self.source_type.app_label, 
                'type': self.source_type.model, 
                'pk': self.source_id, 
            }, 
            'sink': {
                'app': self.sink_type.app_label, 
                'type': self.sink_type.model, 
                'pk': self.sink_id, 
            }
        }
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
        """Get an in-memory source:[sinks] mapping
        
        Note: this does a lot of internal book-keeping to minimize the 
        number of queries performed by loading all targets of a particular
        type at once, then doing a source:sink mapping from that set.
        """
        records = cls.objects.filter(
            fitting_type=fitting_type or cls.DEFAULT_FITTING_TYPE
        ).values( 'sink_type_id','sink_id', 'source_type_id','source_id' )
        type_map = {}
        for record in records:
            type_map.setdefault( record['sink_type_id'],[]).append(record['sink_id'])
            type_map.setdefault( record['source_type_id'],[]).append(record['source_id'])
        cts = dict([(ct.id,ct) for ct in ct_models.ContentType.objects.filter(
            id__in = type_map.keys()
        ).all()])
        
        object_map = {}
        for (contenttype_id,ids) in type_map.items():
            ct = cts.get(contenttype_id)
            if not ct:
                log.warn("Fitting references a deleted content-type")
                continue
            model_cls = ct.model_class()
            query = model_cls.objects.filter(
                pk__in = ids 
            )
            if getattr(model_cls,'default_prefetch',None):
                query = query.prefetch_related( *model_cls.default_prefetch )
            for target in list(query.all()):
                object_map[(contenttype_id,target.id)] = target 
        
        final_mapping = {}
        for record in records:
            source = object_map.get((record['source_type_id'],record['source_id']))
            sink = object_map.get((record['sink_type_id'],record['sink_id']))
            if source and sink:
                final_mapping.setdefault( source,[]).append( sink )
        return final_mapping

class PipeMapping( object ):
    """Cache for in-memory hierarchic structure handling"""
    def __init__(self,mapping=None,fitting_type=None):
        self.fitting_type = fitting_type or Fitting.DEFAULT_FITTING_TYPE
        if mapping is None:
            mapping = Fitting.mapping(fitting_type=self.fitting_type)
        self.mapping = mapping
        self.reverse = {}
        for source,sinks in mapping.items():
            for sink in sinks:
                self.reverse.setdefault(sink,[]).append(source)
    def sources(self,record):
        return self.reverse.get(record,[]) if record.id else []
    def sinks(self,record):
        return self.mapping.get(record,[]) if record.id else []
    def replace(self,record):
        """Replace the given record in our mappings"""
        for source in [self.mapping,self.reverse]:
            for key,value in source.items():
                if key.id == record.id and isinstance(record,key.__class__):
                    del source[key]
                    source[record] = value
                for i,v in enumerate(value):
                    if v.id == record.id and isinstance(record,v.__class__):
                        value[i] = record

def with_cache( *cache_args,**cache_named ):
    """Use a PipeMapping cache on PipeElement to speed up hierarchy-heavy operations
    
    @with_cache()
    def function(records):
        for r in records:
            r.sources()
            for item in r.sinks():
                blah...
    """
    def wrapper( function ):
        @functools.wraps( function )
        def with_wrapper( *args, **named ):
            with cache( *cache_args, **cache_named ):
                return function(*args,**named)
        return with_wrapper 
    return wrapper 

@contextlib.contextmanager
def cache( *args, **named ):
    if not PipeElement._pipe_mapping:
        PipeElement._pipe_mapping = PipeMapping(*args,**named)
        delete = True
    else:
        delete = False
    yield 
    if delete:
        try:
            PipeElement._pipe_mapping = None
        except AttributeError:
            pass
    

class PipeElement(object):
    """Mix-in providing pipe-fitting manipulations
    
    A DEFAULT_FITTING_TYPE is defined, this is the pipe type 
    that will be assumed for these APIs, cases where there 
    is really just one type of pipe can thus ignore the 
    fitting_type arguments entirely.
    """
    _pipe_mapping = None
    DEFAULT_FITTING_TYPE = Fitting.DEFAULT_FITTING_TYPE
    def _sources(self, fitting_type=None):
        return Fitting.sources(self, fitting_type=fitting_type or self.DEFAULT_FITTING_TYPE)
    def sources(self, fitting_type=None):
        """Retrieve all currently fitted sources (the actual objects)"""
        fitting_type=fitting_type or self.DEFAULT_FITTING_TYPE
        if self._pipe_mapping and self._pipe_mapping.fitting_type == fitting_type:
            return self._pipe_mapping.sources( self )
        result = []
        for f in self._sources(fitting_type):
            try:
                result.append( f.source )
            except AttributeError:
                f.delete()
        return result
    def _sinks(self, fitting_type=None):
        return Fitting.sinks(self, fitting_type=fitting_type or self.DEFAULT_FITTING_TYPE)
    def sinks(self, fitting_type=None):
        """Retrieve all current fitted sinks (the actual objects)"""
        fitting_type=fitting_type or self.DEFAULT_FITTING_TYPE
        if self._pipe_mapping and self._pipe_mapping.fitting_type == fitting_type:
            return self._pipe_mapping.sinks( self )
        result = []
        for f in self._sinks(fitting_type):
            try:
                result.append(f.sink)
            except AttributeError:
                f.delete()
        return result
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

    def iter_ancestors(self,fitting_type=None,seen=None):
        seen = seen or set()
        for source in self.sources(fitting_type):
            if source not in seen:
                yield source 
                seen.add(source)
                for anc in source.iter_ancestors( fitting_type, seen ):
                    yield anc 
    def ancestors(self,fitting_type=None):
        return list(self.iter_ancestors(fitting_type))
    def iter_descendants(self,fitting_type=None,seen=None):
        seen = seen or set()
        for source in self.sinks(fitting_type):
            if source not in seen:
                yield source 
                seen.add(source)
                for anc in source.iter_descendants( fitting_type, seen):
                    yield anc 
    def descendants(self,fitting_type=None):
        return list(self.iter_descendants(fitting_type))

from django.db.models.signals import pre_delete
from django.dispatch.dispatcher import receiver
@receiver(pre_delete)
def unlink_fittings_on_deletion(sender, instance=None,  **named):
    """Unlink any fitting registered for a to-delete sender
    
    NOTE: this runs on *every* deletion of *any* record, this 
    is a bit of a huge club to solve a minor issue, but it should
    prevent dangling references and doesn't affect my use cases.
    """
    if getattr( instance, 'no_fittings', None ):
        return 
    if isinstance(instance, PipeElement) and isinstance(instance,models.Model):
        if hasattr( instance, 'fitting_cleanup' ):
            try:
                instance.fitting_cleanup()
            except Exception:
                log.exception("Failure cleaning up %s instance: %s", sender, instance )
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
        try:
            Fitting.objects.filter(source_type=ct, source_id=instance.pk).delete()
            Fitting.objects.filter(sink_type=ct, sink_id =instance.pk).delete()
        except Exception:
            log.exception("Unable to cleanup Fittings after deletion, likely running in a migration")
