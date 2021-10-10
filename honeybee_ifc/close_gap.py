
from ladybug_geometry.geometry3d.line import LineSegment3D
from ladybug_geometry.geometry3d.pointvector import Point3D
from ladybug_geometry.geometry3d.polyface import Polyface3D
from honeybee.room import Room
from honeybee.typing import clean_and_id_string


def line_at_center(center, normal, distance=0.5):
    """Get a line at the center of the face."""
    vector = normal * (distance)
    new_point = center.move(vector)
    return LineSegment3D.from_end_points(center, new_point)


def intersection_point_with_context_polysface(line, polyfaces):
    """If the line interestects with any of the polyfaces, return the 
    interesection point."""
    for polyface in polyfaces:
        if polyface.intersect_line_ray(line):
            return polyface.intersect_line_ray(line)


def convert_to_rhino_points(points):
    return ['{}, {}, {}'.format(point.x, point.y, point.z) for point in points]


def move_polyface_vertices(face_indice, poly_dict, vector):
    vert_indices = set(poly_dict['face_indices'][face_indice][0])

    for indice in vert_indices:
        point = Point3D(poly_dict['vertices'][indice][0], poly_dict['vertices']
                        [indice][1], poly_dict['vertices'][indice][2])
        moved_point = point.move(vector)
        poly_dict['vertices'][indice] = (moved_point.x, moved_point.y, moved_point.z)


def move_faces(room, context_rooms):
    polyface = room.geometry
    context_polyfaces = [room.geometry for room in context_rooms]
    poly_dict = polyface.to_dict()

    faces = Polyface3D.get_outward_faces(polyface.faces, 0.01)
    for count, face in enumerate(faces):

        line = line_at_center(face.center, face.normal)
        intersection_point = intersection_point_with_context_polysface(
            line, context_polyfaces)
        if not intersection_point:
            try:
                # if the area of the mesh face is so small that it can't accommodate
                # 1m x 1m grid
                mesh = face.mesh_grid(1, 1, generate_centroids=True)
            except AssertionError:
                continue
            mesh_face_centers = mesh.face_centroids
            for mesh_face_center in mesh_face_centers:
                line = line_at_center(mesh_face_center, face.normal)

                intersection_point = intersection_point_with_context_polysface(
                    line, context_polyfaces)

                if not intersection_point:
                    continue
                else:
                    distance_to_move = mesh_face_center.distance_to_point(
                        intersection_point[0]) / 2
                    vector = face.normal*(distance_to_move)
                    move_polyface_vertices(count, poly_dict, vector)
                    break
        else:
            distance_to_move = face.center.distance_to_point(intersection_point[0]) / 2
            vector = face.normal*(distance_to_move)
            move_polyface_vertices(count, poly_dict, vector)

    return Polyface3D.from_dict(poly_dict)


def get_gap_closed_rooms(rooms):
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
        moved_polyface = move_faces(room, context_rooms)
        room_to_append = Room.from_polyface3d(rooms[i].display_name, moved_polyface)
        moved_rooms.append(room_to_append)
    return moved_rooms
