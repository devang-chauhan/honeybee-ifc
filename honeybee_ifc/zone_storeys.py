"""This module separates zones in storeys."""
from ladybug_geometry.bounding import bounding_domain_z

polyfaces = [zone.geometry for zone in zones]

z_cords = sorted(list(set([bounding_domain_z([zone.geometry])[0]
                      for zone in zones])), key=lambda x: x)


floor_zones = {z: [] for z in z_cords}

for zone in zones:
    floor_zones[bounding_domain_z([zone.geometry])[0]].append(zone)


rooms = floor_zones[z_cords[floor]]
floors = len(z_cords)
