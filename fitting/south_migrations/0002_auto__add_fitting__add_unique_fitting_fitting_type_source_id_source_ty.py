# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Fitting'
        db.create_table(u'fitting_fitting', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('fitting_type', self.gf('django.db.models.fields.IntegerField')(default=1, db_index=True)),
            ('source_type', self.gf('django.db.models.fields.related.ForeignKey')(related_name='fitting_source_types', to=orm['contenttypes.ContentType'])),
            ('source_id', self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True)),
            ('sink_type', self.gf('django.db.models.fields.related.ForeignKey')(related_name='fitting_sink_types', to=orm['contenttypes.ContentType'])),
            ('sink_id', self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True)),
        ))
        db.send_create_signal(u'fitting', ['Fitting'])

        # Adding unique constraint on 'Fitting', fields ['fitting_type', 'source_id', 'source_type', 'sink_id', 'sink_type']
        db.create_unique(u'fitting_fitting', ['fitting_type', 'source_id', 'source_type_id', 'sink_id', 'sink_type_id'])


    def backwards(self, orm):
        # Removing unique constraint on 'Fitting', fields ['fitting_type', 'source_id', 'source_type', 'sink_id', 'sink_type']
        db.delete_unique(u'fitting_fitting', ['fitting_type', 'source_id', 'source_type_id', 'sink_id', 'sink_type_id'])

        # Deleting model 'Fitting'
        db.delete_table(u'fitting_fitting')


    models = {
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'fitting.fitting': {
            'Meta': {'unique_together': "[('fitting_type', 'source_id', 'source_type', 'sink_id', 'sink_type')]", 'object_name': 'Fitting'},
            'fitting_type': ('django.db.models.fields.IntegerField', [], {'default': '1', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'sink_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'sink_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'fitting_sink_types'", 'to': u"orm['contenttypes.ContentType']"}),
            'source_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'source_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'fitting_source_types'", 'to': u"orm['contenttypes.ContentType']"})
        }
    }

    complete_apps = ['fitting']