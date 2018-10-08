# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='Fitting',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('fitting_type', models.IntegerField(default=1, verbose_name=b'Pipe Type', db_index=True)),
                ('source_id', models.PositiveIntegerField(db_index=True)),
                ('sink_id', models.PositiveIntegerField(db_index=True)),
                ('sink_type', models.ForeignKey(related_name='fitting_sink_types', to='contenttypes.ContentType',on_delete=models.CASCADE)),
                ('source_type', models.ForeignKey(related_name='fitting_source_types', to='contenttypes.ContentType',on_delete=models.CASCADE)),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='fitting',
            unique_together=set([('fitting_type', 'source_id', 'source_type', 'sink_id', 'sink_type')]),
        ),
    ]
