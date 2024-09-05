'''
#==================================================================================================#
# Blendshape Mirrorer
#
# Purpose: Core functions for mirroring blendshapes from one side to another
#          
#
# Dependencies:
#               maya.cmds
#               maya.api.OpenMaya
#
#
# Author: Eric Hug
# Updated: 7/25/2024

'''
#==================================================================================================#
# IMPORT
# built-in python libraries
import os
import json
import logging
from importlib import reload

# 3rd-party
from maya import cmds
from maya.api import OpenMaya as om2


#==================================================================================================#
# VARIABLES
LOG = logging.getLogger(__name__)


#==================================================================================================#
# FUNCTIONS
def import_src_mesh(file_path=""):
    '''Imports the specified obj file and returns the name of the mesh without any namespace
        Parameters:
                    file_path: full file path of the specified mesh
    '''
    mesh_name = ""
    nodes = cmds.file(file_path, 
                      i=True, 
                      force=True,
                      groupReference=False, 
                      mergeNamespacesOnClash=True,
                      removeDuplicateNetworks=True,
                      returnNewNodes=True)
    for each in nodes:
        if cmds.nodeType(each) == "transform":
            mesh_name = each
            break

    return mesh_name


def src_verts(central_vert="", mirror_axis="x"):
    '''Gets and returns the necessary vertices needed for creating the correct vertex order in a mirrored mesh
        Parameters:
                    central_vert: a single vertex Number of the original blendshape mesh that lies along the middle of the mesh.
                    mirror_axis : axis a duplicated mesh is intended to be mirrored across
    '''
    mesh = central_vert.split(".")[0]
    shape = cmds.listRelatives(mesh, shapes=True)[0]
    vert_num = central_vert.split(".")[-1]
    vert_num = vert_num.split("[")[-1]
    vert_num = int(vert_num.split("]")[0])
    sel = om2.MSelectionList()
    sel.add(shape)
    mob = sel.getDependNode(0)
    mesh_verts = om2.MItMeshVertex(mob)
    mesh_verts.setIndex(vert_num)
    vert_ids = mesh_verts.getConnectedVertices()
    vert_positions = []

    # Get positions for each vertex connected to central_vert
    for each in vert_ids:
        full_name = central_vert.replace(str(vert_num), str(each))
        pos = cmds.xform(full_name, query=True, translation=True, worldSpace=True)
        vert_positions.append(pos)

    # Look for the highest vert in the y-axis, 
    # and the highest and lowest verts along the x-axis (for matching vertex orders later)
    up_check = vert_positions[0][1]
    up_vert = vert_ids[0]
    side_check_hi = vert_positions[0][0]
    side_check_lo = vert_positions[0][0]
    side_vert_src = 0
    side_vert_dest = 0
    for num in range(len(vert_ids)):
        if vert_positions[num][1] > up_check:
            up_check = vert_positions[num][1]
            up_vert = vert_ids[num]
        if vert_positions[num][0] > side_check_hi:
            side_check_hi = vert_positions[num][0]
            side_vert_src = vert_ids[num]
        elif vert_positions[num][0] < side_check_lo:
            side_check_lo  = vert_positions[num][0]
            side_vert_dest = vert_ids[num]
    # Desired Values
    src_verts  = [vert_num, up_vert, side_vert_src]
    dest_verts = [vert_num, up_vert, side_vert_dest]

    return[src_verts, dest_verts]


def transfer_vert_order(src_mesh="", dest_mesh="", vertex_ids=[[],[]]):
    '''Transfer the vertex order from the source mesh to the destination mesh
        Parameters:
                    src_mesh   : original mesh
                    dest_mesh  : new_mesh
                    vertex_ids : vertex numbers from original and new mesh
    '''
    src_verts =  ["{}.vtx[{}]".format(src_mesh,  each) for each in vertex_ids[0]]
    dest_verts = ["{}.vtx[{}]".format(dest_mesh, each) for each in vertex_ids[1]]
    cmds.meshRemap(src_verts[0]  , src_verts[1]  , src_verts[2], 
                   dest_verts[0] , dest_verts[1] , dest_verts[2])
    cmds.select(dest_mesh, replace=True)
    cmds.polyNormalPerVertex(freezeNormal=False)
    cmds.select(deselect=True)
    cmds.delete(dest_mesh, 
                constructionHistory=True)
    

def create_mirrored_mesh(mesh="", mirror_axis="x"):
    ''' Duplicates and flips mesh across x-axis
        Parameters:
                    mesh        : mesh user wants to mirror.
                    mirror_axis : axis to mirror duplicated mesh across.
    '''
    new_name = ""
    if "_l_" in mesh:
        new_name = mesh.replace("_l_", "_r_")
    else:
        new_name = mesh.replace("_r_", "_l_")

    cmds.duplicate(mesh, name=new_name)
    cmds.setAttr("{}.s{}".format(new_name, mirror_axis), -1)
    cmds.makeIdentity(new_name, 
                      apply           = True, 
                      scale           = True,
                      normal          = 0,
                      preserveNormals = True)

    return new_name


def export_dest_mesh(mesh="", file_path=""):
    '''Exports mirrored blendshape mesh to specified file path'''
    cmds.select(mesh, replace=True)
    print(file_path)
    cmds.file(file_path, 
              type                = "OBJexport",
              force               = True,
              exportSelected      = True,
              preserveReferences  = True,
              constructionHistory = False,
              options = "groups=1;ptgroups=1;materials=0;smoothing=1;normals=1;")
    cmds.select(deselect=True)

