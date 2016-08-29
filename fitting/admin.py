try:
    from django.contrib import admin
except ImportError as err:
    admin = None 
else:
    from fitting import models 

#    class fittingAdmin( admin.ModelAdmin ):
#        """Admin class"""
#    admin.site.register( models.fitting, fittingAdmin )
