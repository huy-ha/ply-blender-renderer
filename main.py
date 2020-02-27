from argparse import ArgumentParser
import bpy
from os.path import basename, exists
from os import mkdir
import numpy as np


def parse_args():
    parser = ArgumentParser('.ply Blender Renderer')
    parser.add_argument('--input', type=str,
                        help='Path to input .ply file.')
    parser.add_argument('--output',  type=str, default='output/',
                        help='Path to output directory to save output .pngs')
    parser.add_argument('--python',  type=str, default='main.py',
                        help='Blender input python file')
    parser.add_argument('--background',  action='store_true',
                        help='Run Blender headless or not.')
    parser.add_argument('scene_file',
                        help='Base Blender Scene.')
    args = parser.parse_args()
    return args


def setup_scene_settings(resolution=(960, 540)):
    scene = bpy.data.scenes[0]
    scene.cycles.device = 'GPU'
    scene.render.engine = 'CYCLES'
    scene.render.resolution_x = resolution[0]
    scene.render.resolution_y = resolution[1]
    scene.render.resolution_percentage = 100


def load_and_setup_ply(path, output_dir, material):
    """
    Loads a ply file as a blender object,
    and renders it with vertex colors.

    path: path to .ply file
    output_dir: path to the directory to store output .png
    material: blender material to assign to mesh
    """
    file_name = basename(path).split('.')[0]
    if not exists(output_dir):
        mkdir(output_dir)
    output_path = output_dir + file_name + ".png"

    scene = bpy.data.scenes[0]
    scene.render.filepath = output_path

    print("Importing {}. This will take a moment...".format(
        path))
    bpy.ops.import_mesh.ply(filepath=path)
    obj = bpy.data.objects[file_name]

    if obj.data.materials:
        obj.data.materials[0] = material
    else:
        obj.data.materials.append(material)

    # Rescale so that minimum z value (up) is 0
    # and x,y values are between -0.5 and 0.5
    matrix_w = np.matrix(obj.matrix_world)
    vertices_w = [np.squeeze(np.asarray(
        np.matmul(matrix_w, np.array(list(vertex.co) + [1]))))[:3]
        for vertex in obj.data.vertices]

    min_x = min(vertices_w, key=lambda item: item[0])[0]
    max_x = max(vertices_w, key=lambda item: item[0])[0]

    min_y = min(vertices_w, key=lambda item: item[1])[1]
    max_y = max(vertices_w, key=lambda item: item[1])[1]

    min_z = min(vertices_w, key=lambda item: item[2])[2]

    size_x = max_x - min_x
    size_y = max_y - min_y
    max_size = max(size_x, size_y) / 2
    center_x = (max_x + min_x) / 2
    center_y = (max_y + min_y)/2
    obj.location.z = obj.location.z - min_z
    obj.location.y = obj.location.y - center_y/max_size
    obj.location.x = obj.location.x - center_x/max_size
    obj.scale = (1.0/max_size, 1.0/max_size, 1.0/max_size)


if __name__ == "__main__":
    args = parse_args()
    if args.input is None:
        print("Please supply an input .ply path with --input")
        exit()
    vertex_color_shader = bpy.data.materials[0]
    setup_scene_settings()
    load_and_setup_ply(
        path=args.input,
        output_dir=args.output,
        material=vertex_color_shader)
    bpy.ops.render.render(write_still=True)
    exit()
