from django.utils.translation import ugettext_lazy as _
assert _
import logging
#from django.conf.urls.defaults import patterns, include, url
log = logging.getLogger( __name__ )
from . import models

def current_fittings(request,  fitting_type=None,  cls=models.Fitting):
    """Retrieve the full set of current fitting elements
    
    This is a view-fragment intended to allow you to pull the 
    fitting data-set:
    
        return {
            'success': True,
            'fittings': current_fittings( request, fitting_type, cls ),
        }
    """
    fittings = cls.objects
    if fitting_type:
        fittings = fittings.filter( 
            fitting_type=fitting_type, 
        )
    return [ f.__json__() for f in fittings.all() ]

def current_fitting_map(request,  fitting_type=None,  cls=models.Fitting):
    """Retrieve the full set of current fitting elements
    
    This is a view-fragment intended to allow you to pull the 
    fitting data-set:
    
        return {
            'success': True,
            'fittings': current_fittings( request, fitting_type, cls ),
        }
    """
    fittings = cls.objects
    if fitting_type:
        fittings = fittings.filter( 
            fitting_type=fitting_type, 
        )
    mapping = {}
    for fitting in fittings.objects.all():
        mapping.setdefault(
            (fitting.source.app_label, fitting.source.model,  fitting.source_id), 
            []
        ).append( fitting.__json__() )
    return mapping


from django.utils.translation import ugettext as _
assert _
