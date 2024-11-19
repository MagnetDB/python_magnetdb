from django.db import models


class Part(models.Model):
    class Meta:
        db_table = 'parts'
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True, null=False)
    description = models.TextField(null=True)
    type = models.CharField(max_length=255, null=False)
    status = models.CharField(max_length=255, null=False)
    material = models.ForeignKey('Material', on_delete=models.CASCADE, null=False)
    created_at = models.DateTimeField(auto_now_add=True, null=False)
    updated_at = models.DateTimeField(auto_now=True, null=False)
    design_office_reference = models.CharField(max_length=255, null=True)

    def allow_geometry_types(self):
        if self.type == 'helix':
            return ['default', 'salome', 'catia', 'cam', 'shape']
        elif self.type == 'supra':
            return ['default', 'hts']
        return ['default']
