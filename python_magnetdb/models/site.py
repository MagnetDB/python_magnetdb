from django.db import models


class Site(models.Model):
    class Meta:
        db_table = "sites"

    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True, null=False)
    description = models.TextField(null=True)
    status = models.CharField(max_length=255, null=False)
    config_attachment = models.ForeignKey("StorageAttachment", on_delete=models.SET_NULL, null=True)
    metadata = models.JSONField(default=dict, null=False)
    created_at = models.DateTimeField(auto_now_add=True, null=False)
    updated_at = models.DateTimeField(auto_now=True, null=False)

    @property
    def geometry_config_to_json(self):
        """
        Convert site configuration to JSON string.

        Creates a python_magnetgeo MSite object from the site data,
        and returns the JSON representation using the object's to_json() method.

        Returns:
            str: JSON string representation of the MSite
        """
        from python_magnetgeo.deserialize import unserialize_object
        import json

        # Build config dictionary with MSite structure
        config = {
            "__classname__": "MSite",
            "name": self.name,
            "magnets": [],
            "screens": None,
            "z_offset": [],
            "r_offset": [],
            "paralax": [],
        }

        # Populate from related sitemagnet objects
        for site_magnet in self.sitemagnet_set.all():
            # Get the magnet's geometry as JSON, then deserialize to object
            magnet_json = site_magnet.magnet.geometry_config_to_json()
            magnet_obj = unserialize_object(json.loads(magnet_json))
            config["magnets"].append(magnet_obj)
            config["z_offset"].append(site_magnet.z_offset)
            config["r_offset"].append(site_magnet.r_offset)
            config["paralax"].append(site_magnet.parallax)

        # Create MSite object and use its to_json() method
        obj = unserialize_object(config)
        return obj.to_json()

    @property
    def geometry_config_to_yaml(self):
        """
        Convert site configuration to YAML string.

        Creates a python_magnetgeo MSite object from the site data,
        and returns the YAML representation using yaml.dump().

        Returns:
            str: YAML string representation of the MSite
        """
        from python_magnetgeo.deserialize import unserialize_object
        import yaml
        import json

        # Build config dictionary with MSite structure
        config = {
            "__classname__": "MSite",
            "name": self.name,
            "magnets": [],
            "screens": None,
            "z_offset": [],
            "r_offset": [],
            "paralax": [],
        }

        # Populate from related sitemagnet objects
        for site_magnet in self.sitemagnet_set.all():
            # Get the magnet's geometry as JSON, then deserialize to object
            magnet_json = site_magnet.magnet.geometry_config_to_json()
            magnet_obj = unserialize_object(json.loads(magnet_json))
            config["magnets"].append(magnet_obj)
            config["z_offset"].append(site_magnet.z_offset)
            config["r_offset"].append(site_magnet.r_offset)
            config["paralax"].append(site_magnet.parallax)

        # Create MSite object and use yaml.dump()
        obj = unserialize_object(config)
        return yaml.dump(obj, sort_keys=False)
