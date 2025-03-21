# Generated by Django 5.1.3 on 2024-11-26 13:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('python_magnetdb', '0005_remove_simulation_resource_id_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='magnet',
            name='cad_attachments',
        ),
        migrations.RemoveField(
            model_name='magnet',
            name='magnet_parts',
        ),
        migrations.RemoveField(
            model_name='magnet',
            name='parts',
        ),
        migrations.RemoveField(
            model_name='magnet',
            name='simulations',
        ),
        migrations.RemoveField(
            model_name='magnet',
            name='site_magnets',
        ),
        migrations.RemoveField(
            model_name='magnet',
            name='sites',
        ),
        migrations.RemoveField(
            model_name='material',
            name='parts',
        ),
        migrations.RemoveField(
            model_name='part',
            name='cad_attachments',
        ),
        migrations.RemoveField(
            model_name='part',
            name='geometries',
        ),
        migrations.RemoveField(
            model_name='part',
            name='magnet_parts',
        ),
        migrations.RemoveField(
            model_name='part',
            name='magnets',
        ),
        migrations.RemoveField(
            model_name='simulation',
            name='currents',
        ),
        migrations.RemoveField(
            model_name='site',
            name='cad_attachments',
        ),
        migrations.RemoveField(
            model_name='site',
            name='magnets',
        ),
        migrations.RemoveField(
            model_name='site',
            name='records',
        ),
        migrations.RemoveField(
            model_name='site',
            name='simulations',
        ),
        migrations.RemoveField(
            model_name='site',
            name='site_magnets',
        ),
        migrations.AlterField(
            model_name='auditlog',
            name='resource_type',
            field=models.TextField(),
        ),
    ]
