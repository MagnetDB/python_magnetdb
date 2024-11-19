from python_magnetdb.models.site import Site
from python_magnetdb.models.magnet import Magnet
from python_magnetdb.models.material import Material


def format_material(material):
    return {
        "Tref": material.t_ref,
        "VolumicMass": material.volumic_mass,
        "alpha": material.alpha,
        "ElectricalConductivity": material.electrical_conductivity,
        "MagnetPermeability": material.magnet_permeability,
        "Poisson": material.poisson,
        "Rpe": material.rpe,
        "SpecificHeat": material.specific_heat,
        "ThermalConductivity": material.thermal_conductivity,
        "Young": material.young,
        "CoefDilatation": material.expansion_coefficient,
        "nuance": material.nuance,
    }


def generate_magnet_config(magnet_id):
    magnet = Magnet.objects.prefetch_related(
        'magnetpart_set__part__partgeometry_set__attachment',
        'magnetpart_set__part__material',
        'sitemagnet_set__site',
        'geometry_attachment',
    ).get(id=magnet_id)
    print(
        f"generate_magnet_config[{magnet_id}]: magnet={magnet.name}, geometry={magnet.geometry_attachment}"
    )
    payload = {"geom": magnet.geometry_attachment.filename}
    insulator_payload = format_material(Material.objects.get(name="MAT_ISOLANT"))
    for magnet_part in magnet.magnetpart_set.all():
        # if not magnet_part.active:
        #     continue
        if magnet_part.part.type.capitalize() not in payload:
            payload[magnet_part.part.type.capitalize()] = []
        geom = None
        for geometry in magnet_part.part.partgeometry_set.all():
            if geometry.type == "default":
                geom = geometry.attachment.filename
        payload[magnet_part.part.type.capitalize()].append(
            {
                "geom": geom,
                "material": format_material(magnet_part.part.material),
                "insulator": insulator_payload,
            }
        )
    # print(f'generate_magnet_config: {payload}')
    return payload


def generate_site_config(site_id):
    site = Site.objects.prefetch_related("sitemagnet_set").get(id=site_id)
    payload = {"name": site.name, "magnets": []}
    for site_magnet in site.sitemagnet_set.all():
        print(
            f"generate_site_config({site_id}): magnet={site_magnet}, site_magnet={site_magnet.active}"
        )
        # if not site_magnet.active:
        #     continue
        payload["magnets"].append(generate_magnet_config(site_magnet.magnet_id))
    # print(f'generate_site_config: {payload}')
    return payload


def generate_simulation_config(simulation):
    if simulation.magnet_id is not None:
        return generate_magnet_config(simulation.magnet_id)
    elif simulation.site_id is not None:
        return generate_site_config(simulation.site_id)
    raise Exception("Unsupported resource type")
