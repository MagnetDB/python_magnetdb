from django.db import models


class Material(models.Model):
    class Meta:
        db_table = 'materials'
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True, null=False)
    nuance = models.CharField(max_length=255, null=True)
    description = models.TextField(null=True)
    t_ref = models.FloatField(default=20, null=False)
    volumic_mass = models.FloatField(default=0, null=False)
    alpha = models.FloatField(default=0, null=False)
    specific_heat = models.FloatField(default=0, null=False)
    electrical_conductivity = models.FloatField(default=0, null=False)
    thermal_conductivity = models.FloatField(default=0, null=False)
    magnet_permeability = models.FloatField(default=0, null=False)
    young = models.FloatField(default=0, null=False)
    poisson = models.FloatField(default=0, null=False)
    expansion_coefficient = models.FloatField(default=0, null=False)
    rpe = models.FloatField(null=False)
    metadata = models.JSONField(default=dict, null=False)
    created_at = models.DateTimeField(auto_now_add=True, null=False)
    updated_at = models.DateTimeField(auto_now=True, null=False)
