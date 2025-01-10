# Generated by Django 5.1.4 on 2024-12-19 13:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('python_magnetdb', '0008_alter_part_hts_attachment_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='magnetpart',
            name='angle',
            field=models.FloatField(null=True),
        ),
        migrations.AddField(
            model_name='magnetpart',
            name='inner_bore',
            field=models.FloatField(null=True),
        ),
        migrations.AddField(
            model_name='magnetpart',
            name='outer_bore',
            field=models.FloatField(null=True),
        ),
        migrations.DeleteModel(
            name='PartGeometry',
        ),
    ]
