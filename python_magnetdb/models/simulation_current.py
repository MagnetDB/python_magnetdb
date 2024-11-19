from django.db import models


class SimulationCurrent(models.Model):
    class Meta:
        db_table = 'simulation_currents'
    id = models.BigAutoField(primary_key=True)
    simulation = models.ForeignKey('Simulation', on_delete=models.CASCADE, null=False)
    magnet = models.ForeignKey('Magnet', on_delete=models.CASCADE, null=False)
    value = models.FloatField(null=False)
    created_at = models.DateTimeField(auto_now_add=True, null=False)
    updated_at = models.DateTimeField(auto_now=True, null=False)
