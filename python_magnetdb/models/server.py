from django.db import models


class Server(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255, null=False)
    user = models.ForeignKey('User', on_delete=models.CASCADE, null=False)
    username = models.CharField(max_length=255, null=False)
    host = models.CharField(max_length=255, null=False)
    private_key = models.TextField(null=False)
    public_key = models.TextField(null=False)
    created_at = models.DateTimeField(auto_now_add=True, null=False)
    updated_at = models.DateTimeField(auto_now=True, null=False)
    image_directory = models.CharField(max_length=255, null=False)
    type = models.CharField(max_length=255, default='compute', null=False)
    smp = models.BooleanField(default=True, null=False)
    multithreading = models.BooleanField(default=True, null=False)
    cores = models.IntegerField(default=1, null=False)
    dns = models.CharField(max_length=255, default='localhost', null=False)
    job_manager = models.CharField(max_length=255, default='none', null=False)
    mesh_gems_directory = models.CharField(max_length=255, default='/opt/MeshGems', null=False)

    class Meta:
        db_table = 'servers'
