from django.db import models


class User(models.Model):
    class Meta:
        db_table = 'users'
    id = models.BigAutoField(primary_key=True)
    username = models.CharField(max_length=255, unique=True, null=False)
    email = models.CharField(max_length=255, null=False)
    name = models.CharField(max_length=255, null=False)
    role = models.CharField(max_length=255, default='guest', null=False)
    created_at = models.DateTimeField(auto_now_add=True, null=False)
    updated_at = models.DateTimeField(auto_now=True, null=False)
    api_key = models.CharField(max_length=255, unique=True)

    def is_authorize(self, action: str) -> bool:
        if self.role == 'guest':
            return action in ['read']
        elif self.role == 'user':
            return action in ['read', 'update', 'delete']
        elif self.role == 'designer':
            return action in ['create', 'read', 'update', 'delete']
        elif self.role == 'admin':
            return action in ['create', 'read', 'update', 'delete', 'admin']
        return False
