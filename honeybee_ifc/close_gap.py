from ladybug_geometry.geometry3d.line import LineSegment3D
from ladybug_geometry.geometry3d.pointvector import Point3D
from ladybug_geometry.geometry3d.polyface import Polyface3D
from honeybee.room import Room
from honeybee.typing import clean_and_id_string


def line_at_center(center, normal, distance=0.5):
    """Get a 0.5m long line at the center of the face in the direction of the normal."""
    vector = normal * (distance)
    new_point = center.move(vector)
    return LineSegment3D.from_end_points(center, new_point)


def intersect_point_with_context_polysface(line, polyfaces):
    """If the line interestects with any of the polyfaces, return the 
    interesection point."""
    for polyface in polyfaces:
        if polyface.intersect_line_ray(line):
            return polyface.intersect_line_ray(line)


def convert_to_rhino_points(points):
    return ['{}, {}, {}'.format(point.x, point.y, point.z) for point in points]


def move_polyface_vertices(face_indice, poly_dict, vector):
    """Move vertices of a polyface using a vector.

    Args:
        face_indice: A list of face indices. A face indice is a tuple of integers.
            each integer refers to a point in the key named "vertices" in the dictionary.
        poly_dict: A dictionary representing a polyface.
        vector: A ladybug_geometry.Vector3D.

    Returns:
        None
    """
    # get unique vertices from all the indices in the list of indices provided to this
    # function
    vert_indices = []
    for indice in face_indice:
        vert_indices.extend(list(poly_dict['face_indices'][indice][0]))
    vert_indices = list(set(vert_indices))

    # for each indice, get the point from the polyface dictionary and move it along
    # the vector
    for indice in vert_indices:
        point = Point3D(poly_dict['vertices'][indice][0], poly_dict['vertices']
                        [indice][1], poly_dict['vertices'][indice][2])
        moved_point = point.move(vector)
        poly_dict['vertices'][indice] = (moved_point.x, moved_point.y, moved_point.z)


def move_faces_in_polyface(room, context_rooms):
    """Move faces of a room outwards.

    For each face of the room, intersection is checked with the context rooms. If an 
    intersection is found, the face is moved outwards by half of the distance between the
    face and the intersection room.

    To check intersection, a 0.5m long line is created from the center of each face. The
    line is created in the direction of the normal of the face.
    """

    polyface = room.geometry
    poly_dict = polyface.to_dict()
    context_polyfaces = [room.geometry for room in context_rooms]

    iterator = enumerate(polyface.faces)
    for face_count, face in iterator:

        # If the next face in the interator is coplanar to the current face, select both
        # the faces for moving outwards.
        if face_count < len(polyface.faces)-1:
            if face.plane.is_coplanar_tolerance(polyface.faces[face_count + 1].plane, 0.01, 0):
                face_count = [face_count, face_count + 1]
            else:
                face_count = [face_count]
        else:
            face_count = [face_count]

        # create a 0.5m long line at the center of the face
        line = line_at_center(face.center, face.normal)
        # find intersection with the context rooms
        intersection_point = intersect_point_with_context_polysface(
            line, context_polyfaces)

        # For a face, if interesection is not found, mesh the face amd check interesection
        # using the mesh face centers.
        # TODO: There's an opportunity here to use recursion
        if not intersection_point:
            try:
                mesh = face.mesh_grid(1, 1, generate_centroids=True)
            except AssertionError:
                continue

            mesh_face_centers = mesh.face_centroids

            for mesh_face_center in mesh_face_centers:
                line = line_at_center(mesh_face_center, face.normal)
                intersection_point = intersect_point_with_context_polysface(
                    line, context_polyfaces)
                if not intersection_point:
                    continue
                else:
                    distance_to_move = mesh_face_center.distance_to_point(
                        intersection_point[0]) / 2
                    vector = face.normal*(distance_to_move)
                    move_polyface_vertices(face_count, poly_dict, vector)
                    break

        # if intersection is found, move the face outwards by half of the distance between
        else:
            distance_to_move = face.center.distance_to_point(intersection_point[0]) / 2
            vector = face.normal*(distance_to_move)
            move_polyface_vertices(face_count, poly_dict, vector)

        # if a face and it's next face are coplanar, both are moved outwards already
        # therefore, skip the next face
        if len(face_count) > 1:
            next(iterator, None)

    return Polyface3D.from_dict(poly_dict)


moved_rooms = []
for i in range(len(rooms)):
    # making a copy so that original list of rooms are not altered
    rooms_copy = [room for room in rooms]
    # room in a list of rooms
    room = rooms_copy[i]
    # remove the above room from the list
    rooms_copy.pop(i)
    # list of the rest of the rooms
    context_rooms = rooms_copy
    moved_polyface = move_faces_in_polyface(room, context_rooms)
    room_to_append = Room.from_polyface3d(clean_and_id_string('Room'), moved_polyface)
    moved_rooms.append(room_to_append)
