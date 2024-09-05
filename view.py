'''
#==================================================================================================#
# Blendshape Mirrorer
#
# Purpose: UI for mirroring blendshapes from one side to another
#          
#
# Dependencies:
#               maya.cmds
#               PySide2
#
#
# Author: Eric Hug
# Updated: 7/25/2024
'''
#==================================================================================================#
# IMPORT
# built-in python libraries
import os
import sys
import logging
from importlib import reload

# 3rd-party
from maya import cmds, OpenMayaUI
from PySide2 import QtWidgets, QtCore, QtGui
from shiboken2 import wrapInstance


from blendshape_mirrorer import core
reload(core)


#==================================================================================================#
# VARIABLES
LOG = logging.getLogger(__name__)
TEXTFIELD_STYLESHEET_ACTIVE = '''
QPushButton {
    background: #555;
    color: lightgrey;
}

QPushButton:hover {
    color: white;
    background: #666;
}
'''
TEXTFIELD_STYLESHEET_INACTIVE = '''
QLabel {
    color:rgb(135,135,135);
}

QLineEdit {
    background: rgb(76,76,76); 
    color:rgb(135,135,135);
}
'''

#==================================================================================================#
# FUNCTIONS
def start_up(width=720, height=258):
    '''Start Function for user to run the tool.'''
    win = get_maya_main_window()
    for each in win.findChildren(QtWidgets.QWidget):
        if each.objectName() == "MirrorBlendShapeTool":
            each.deleteLater()
    tool = MirrorBlendShapeTool(parent=win)
    tool.resize(width, height)
    tool.show()

    return tool

def get_maya_main_window():
    '''Locates Main Window, so we can parent our tool to it.'''
    maya_window_ptr = OpenMayaUI.MQtUtil.mainWindow()

    return wrapInstance(interpret_int_long(maya_window_ptr), QtWidgets.QWidget)

def interpret_int_long(value):
    if int(sys.version.split(" ")[0][0]) > 2:
        return int(value)
    else:
        return long(value)
#==================================================================================================#
# CLASSES
class MirrorBlendShapeTool(QtWidgets.QWidget):
    """
    Purpose:
       This tool is used in Maya to create mirrored blendshapes for the purpose of sending them back to ZBrush 
       so correctives and combination shapes can be created within the respective program.

       Why ZBrush?
       While it's true Maya can create mirrored blendshapes within its shape editor, its sculpting tools unfortunately are not as user-friendly as ZBrush's for creating blendshapes.
    """

    def __init__(self, parent=None):
        super(MirrorBlendShapeTool, self).__init__(parent=parent)
        self.directory_path = ""
        # ----------- #
        # Base Window #
        # ----------- #
        self.setWindowTitle("MirrorBlendShapeTool")
        self.setObjectName("MirrorBlendShapeTool")
        self.main_layout = QtWidgets.QVBoxLayout()
        self.main_layout.setSpacing(6)
        self.main_layout.setContentsMargins(QtCore.QMargins(0, 0, 0, 0))
        self.setLayout(self.main_layout)
        # Menu
        self.menu_bar = QtWidgets.QMenuBar()
        self.menu = QtWidgets.QMenu("File")
        self.menu_actions = [QtWidgets.QAction("Import Mesh"), 
                             QtWidgets.QAction("Export Selected Mesh")]
        self.menu_bar.addMenu(self.menu)
        for each in self.menu_actions:
            self.menu.addAction(each)
        self.menu_actions[0].triggered.connect(self.import_mesh)
        self.menu_actions[1].triggered.connect(self.export_mesh)
        self.components_widget   = BasicWidget(layout_type="vertical", 
                                               spacing=6, 
                                               margins=[6,0,6,6], 
                                               h_align="left", 
                                               v_align="top")
        # Menu Separator
        self.menu_separator = QtWidgets.QFrame()
        self.menu_separator.setLineWidth(1)
        self.menu_separator.setFrameShape(QtWidgets.QFrame.HLine)
        # Vertex Checker Widget
        self.vert_checker_widget = BasicWidget(layout_type="horizontal", 
                                               spacing=6, 
                                               margins=[0,0,0,0], 
                                               h_align="left", 
                                               v_align="top")
        self.vert_label          = QtWidgets.QLabel("Vertex Number:")
        self.spacer              = QtWidgets.QSpacerItem(6,6)
        self.vert_textfield      = QtWidgets.QLineEdit()
        self.vert_btn            = QtWidgets.QPushButton("Selected Vertex")
        self.vert_textfield.setFixedHeight(35)
        self.vert_btn.setFixedHeight(35)
        self.vert_btn.setFixedWidth(124)
        self.vert_checker_widget.layout.addWidget(self.vert_label)
        self.vert_checker_widget.layout.addItem(self.spacer)
        self.vert_checker_widget.layout.addWidget(self.vert_textfield)
        self.vert_checker_widget.layout.addWidget(self.vert_btn)
        self.vert_checker_widget.setStyleSheet(TEXTFIELD_STYLESHEET_ACTIVE)
        self.vert_textfield.setPlaceholderText("(Vertex along central edgeloop of Imported Mesh)")
        self.vert_btn.clicked.connect(self.get_vertex_number)
        # Vertex Checker Separator
        self.vert_separator = QtWidgets.QFrame()
        self.vert_separator.setLineWidth(1)
        self.vert_separator.setFrameShape(QtWidgets.QFrame.HLine)
        # Mirror Axis Setting
        self.options_label = QtWidgets.QLabel("Build Options:")
        self.options_label.setAlignment(QtCore.Qt.AlignHCenter)
        self.mirror_axis_widget = BasicWidget(layout_type="horizontal", 
                                              spacing=6, 
                                              margins=[0,0,0,0], 
                                              h_align="left", 
                                              v_align="top")
        self.mirror_axis_label = QtWidgets.QLabel("Mirror Axis:")
        self.mirror_axis_cbox_list = CheckBoxList(vertical = False, 
                                                  names    = ["x", "y", "z"], 
                                                  type     = "radiobutton")
        self.vert_end_spacer = QtWidgets.QSpacerItem(6,6, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.mirror_axis_cbox_list.item_dict["x"].setChecked(True)
        self.mirror_axis_widget.layout.addWidget(self.mirror_axis_label)
        self.mirror_axis_widget.layout.addWidget(self.mirror_axis_cbox_list)
        self.mirror_axis_widget.layout.addItem(self.vert_end_spacer)
        # Export Option
        self.export_widget = BasicWidget(layout_type="horizontal", 
                                         spacing=6, 
                                         margins=[0,0,0,0], 
                                         h_align="left", 
                                         v_align="top")
        self.export_label = QtWidgets.QLabel("Export Mesh on Build:")
        self.export_cbox = QtWidgets.QCheckBox()
        self.export_cbox.setChecked(True)
        self.export_label.setBuddy(self.export_cbox)
        self.export_cbox.stateChanged.connect(self.export_settings_active)
        self.export_end_spacer = QtWidgets.QSpacerItem(6,6, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.export_widget.layout.addWidget(self.export_label)
        self.export_widget.layout.addWidget(self.export_cbox)
        self.export_widget.layout.addItem(self.export_end_spacer)
        # Export Directory
        self.export_dir_widget   = BrowseWidget(label="Export Directory:",
                                                search_type="directory")
        self.export_dir_widget.browse_btn.setFixedWidth(124)
        self.export_dir_widget.setContentsMargins(QtCore.QMargins(12, 0, 0, 0))
        self.export_dir_widget.setStyleSheet(TEXTFIELD_STYLESHEET_ACTIVE)
        # Build Options Separator
        self.build_separator = QtWidgets.QFrame()
        self.build_separator.setLineWidth(1)
        self.build_separator.setFrameShape(QtWidgets.QFrame.HLine)
        # Build Mirror Mesh
        self.final_btns_widget = BasicWidget(layout_type="horizontal", 
                                             spacing=6, 
                                             margins=[0,0,0,0], 
                                             h_align="left", 
                                             v_align="top")
        self.new_import_btn = QtWidgets.QPushButton("New Blendshape")
        self.build_btn      = QtWidgets.QPushButton("Build")
        self.build_btn.clicked.connect(self.build)
        self.new_import_btn.clicked.connect(self.new_blendshape)
        self.final_btns_widget.layout.addWidget(self.new_import_btn)
        self.final_btns_widget.layout.addWidget(self.build_btn)
        self.new_import_btn.setToolTip("Start a new mirrored blendshape after current one is built and exported.")
        # Assemble Components
        self.main_layout.addWidget(self.menu_bar)
        self.main_layout.addWidget(self.menu_separator)
        self.components_widget.layout.addWidget(self.vert_checker_widget)
        self.components_widget.layout.addWidget(self.vert_separator)
        self.components_widget.layout.addWidget(self.mirror_axis_widget)
        self.components_widget.layout.addWidget(self.options_label)
        self.components_widget.layout.addWidget(self.mirror_axis_widget)
        self.components_widget.layout.addWidget(self.export_widget)
        self.components_widget.layout.addWidget(self.export_dir_widget)
        self.components_widget.layout.addWidget(self.build_separator)
        self.components_widget.layout.addWidget(self.final_btns_widget)
        self.main_layout.addWidget(self.components_widget)
        # Finalize
        self.setWindowFlags(QtCore.Qt.Window)

    def build(self):
        '''Creates the mirrored blendshape. 
            NOTE:
                1. Mesh vertex must either be selected in the scene or set in the "Vertex Number" textfield (self.vert_textfield). 
                   (Ideally a vertex not modified by the blendshape that runs down the center of the mesh)
                2. If export directory not specified, popup window will appear and ask user for one.
        '''
        if self.vert_textfield.text() == "":
            if cmds.ls(selection=True, flatten=True)[0]:
                central_vert = cmds.ls(selection=True, flatten=True)[0]
                mesh = central_vert.split(".")[0]
            else: LOG.error("No single vertex specified in textfield, nor single vertex selected in scene.")
        elif cmds.objExists(self.vert_textfield.text()) == False:
            LOG.error("String in textfield is a vertex that does not exist. Check if there\'s quotes in textfield.")
        else:
            central_vert = self.vert_textfield.text()
            mesh = central_vert.split(".")[0]

        # duplicate mesh, flip mesh across x-axis, freeze scale transformation
        new_mesh = core.create_mirrored_mesh(mesh=mesh)
        # get vertices for transferring vertex order
        needed_verts = core.src_verts(central_vert=central_vert)
        # transfer vertex order
        core.transfer_vert_order(src_mesh   = mesh, 
                                 dest_mesh  = new_mesh, 
                                 vertex_ids = needed_verts)
        # export new mesh as opposite side blendshape
        # if preview setting checked, do not export
        if self.export_cbox.isChecked():
            self.directory_path = self.export_dir_widget.file_path_line.text()
            if os.path.isdir(self.directory_path):
                full_path = "{}/{}".format(self.directory_path, new_mesh)
                core.export_dest_mesh(mesh      = new_mesh, 
                                      file_path = full_path)
            else:
                self.directory_path = self.browse_directory()
                full_path = "{}/{}".format(self.directory_path, new_mesh)
                core.export_dest_mesh(mesh      = new_mesh, 
                                      file_path = full_path)

    def get_vertex_number(self):
        '''Get central vertex for mirroring purposes'''
        vert = cmds.ls(selection=True, flatten=True)[0]
        self.vert_textfield.setText(vert)

    def import_mesh(self):
        '''Import blendshape mesh and frame in viewport'''
        # Get file path
        file_path = self.browse_command().replace("\'", "")
        mesh_name = file_path.split("/")[-1].replace(".obj","")
        src_dir   = file_path.split(mesh_name)[0]
        if cmds.objExists(mesh_name):
            cmds.delete(mesh_name)
        # Import file
        mesh = core.import_src_mesh(file_path=file_path).split("|")[-1]
        if mesh != mesh_name:
            cmds.rename(mesh, mesh_name)
        # set directory for exporting
        self.directory_path = src_dir
        self.export_dir_widget.file_path_line.setText(src_dir)
        # frame mesh in viewport
        curCamera="persp"
        for vp in cmds.getPanel(type="modelPanel"):
            curCamera=cmds.modelEditor(vp,q=1,av=1,cam=1)
        cmds.select(mesh_name, replace=True)
        cmds.viewFit(curCamera, fitFactor=1)

    def export_mesh(self):
        '''Export function for Menu Action'''
        mesh = cmds.ls(selection=True)[0]
        file_path = QtWidgets.QFileDialog.getSaveFileName(self,
                                                          dir="{}{}".format(self.directory_path, mesh),
                                                          caption="Save Blendshape Mesh",
                                                          filter="Object Files (*.obj);;" )
        # get full file path data from tuple
        new_string = list(file_path)[0]
        new_string = new_string.replace("[", "").replace("]", "")
        new_string = new_string.replace(".obj", "")
        # Call core export function
        core.export_dest_mesh(mesh=mesh, 
                              file_path=new_string)
    
    def browse_command(self):
        '''Get and return file path to use for importing blendshape mesh'''
        self.sel_file = QtWidgets.QFileDialog.getOpenFileName(self,
                                                              dir=self.directory_path,
                                                              caption="Get Blendshape Mesh",
                                                              filter="Object Files (*.obj);;" )
        # get full file path data from tuple
        new_string = list(self.sel_file)
        new_string.pop(-1)
        new_string = str(new_string).replace("[", "").replace("]", "")

        return new_string
    
    def browse_directory(self):
        '''Choose Directory path if one does not exist in export-textfield'''
        self.sel_file = QtWidgets.QFileDialog.getExistingDirectory(self,
                                                                   caption="Choose Directory",
                                                                   options=QtWidgets.QFileDialog.ShowDirsOnly)
        return self.sel_file

    def export_settings_active(self):
        '''Sets whether export textfield is active depending on checkbox state'''
        if self.export_cbox.isChecked():
            self.export_dir_widget.file_path_line.setReadOnly(False)
            self.export_dir_widget.file_path_line.setEnabled(True)
            self.export_dir_widget.browse_btn.setEnabled(True)
            self.export_dir_widget.setStyleSheet(TEXTFIELD_STYLESHEET_ACTIVE)
        else:
            self.export_dir_widget.file_path_line.setReadOnly(True)
            self.export_dir_widget.file_path_line.setEnabled(False)
            self.export_dir_widget.browse_btn.setEnabled(False)
            self.export_dir_widget.setStyleSheet(TEXTFIELD_STYLESHEET_INACTIVE)
    
    def new_blendshape(self):
        '''Creates a new scene and imports a new blendshape for the user to mirror'''
        cmds.file(newFile=True, force=True)
        self.import_mesh()
            

class BrowseWidget(QtWidgets.QWidget):
    def __init__(self, parent=None, label="", search_type=None, file_types=None, currentTab=1):
        super(BrowseWidget, self).__init__(parent=parent)
        ''' Creates a widget that allows a user to browse 
            and return a folder directory into a textfield.

        label: text that will appear before textfield.
        search_type: Method of Browsing. Locate existing file(s), directory(s) or saving a file.
                     Valid Arguments: 'saveFile', 'file', 'files', 'directory'
        file_types: List of file types you want to see while browsing.

        Example:
        from ui_library import ui_library as ui_parts
        test_widget = ui_parts.BrowseWidget(label="Choose File:",
                                            search_type="file",
                                            file_types="Text Files (*.txt);; Image Files (*.jpg *.jpeg *.png *.tif)" 
                                            )
        test_widget.show()
        '''
        self.label = label
        self.file_types = file_types
        self.search_type = search_type

        # Set Search to single file if search_type left blank
        if self.file_types and self.search_type == None:
            self.search_type = "file"

        ### Building UI
        # Base Window
        self.resize(400, 50)
        self.main_layout = QtWidgets.QHBoxLayout()
        self.margins = QtCore.QMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(6)
        self.main_layout.setContentsMargins(self.margins)
        self.setLayout(self.main_layout)

        ## Browse Setup
        # Label
        self.browse_label = QtWidgets.QLabel(self.label)
        self.main_layout.addWidget(self.browse_label)
        # Textfield
        self.file_path_line = QtWidgets.QLineEdit()
        self.file_path_line.setFixedHeight(35)
        self.main_layout.addWidget(self.file_path_line)
        # Button
        self.browse_btn = QtWidgets.QPushButton("Browse")
        # # self.browse_file_icon = qta.icon("fa5s.folder-open", color="lightgrey")
        # self.browse_btn = QtWidgets.QPushButton(self.browse_file_icon, "")
        self.browse_btn.setFixedHeight(35)
        # self.browse_btn.setFixedWidth(35)
        self.browse_btn.clicked.connect(self.browse_command)
        self.main_layout.addWidget(self.browse_btn)

    def browse_command(self):
        '''When Browse Button pressed, allows user to select a folder,
           and returns folder path into textfield.
        '''
        # Determine Search Type
        if self.search_type == "saveFile":
            self.sel_file = QtWidgets.QFileDialog.getSaveFileName(self,
                                                                  caption="save file",
                                                                  filter=self.file_types)
        elif self.search_type == "file":
            self.sel_file = QtWidgets.QFileDialog.getOpenFileName(self,
                                                                  caption="get file",
                                                                  filter=self.file_types)
        elif self.search_type == "files":
            self.sel_file = QtWidgets.QFileDialog.getOpenFileNames(self,
                                                                   caption="get files",
                                                                   filter=self.file_types)
        elif self.search_type == "directory":
            self.sel_file = QtWidgets.QFileDialog.getExistingDirectory(self,
                                                                       caption="Choose Directory",
                                                                       options=QtWidgets.QFileDialog.ShowDirsOnly)
        else:
            LOG.error("Invalid argument \'{}\' for parameter: \'search_type\'."
                      "\nValid options: \'file\', \'files\', \'directory\'".format(self.search_type))
            return

        # Return path to textfield
        if isinstance(self.sel_file, tuple):
            # Use for 'file' or 'files'
            new_string = list(self.sel_file)
            new_string.pop(-1)
            new_string = str(new_string).replace("[", "").replace("]", "")
            self.file_path_line.setText(new_string)
        elif isinstance(self.sel_file, str):
            # Use for 'directory'
            self.file_path_line.setText(self.sel_file)
        else:
            LOG.error("Data type being returned to textfield is not converted to string.")
            return


class CheckBoxList(QtWidgets.QWidget):
    '''Add a widget with a list of checkboxes to your ui.
    Args:
        vertical: Direction the checkboxes appear. True aligns vertically. Otherwise horizontal. True is Default.
        names:    List of strings that create the labels for each checkbox.
        type:     Type of component widget will be containing.
                      Valid Options: "checkbox", "radiobutton", "button"
    '''
    def __init__(self, parent=None, vertical=True, names=["checkbox_01","checkbox_02"], type="checkbox"):
        super(CheckBoxList, self).__init__(parent)
        self.vertical =  vertical
        self.names =     names
        self.type =      type
        self.item_dict = {}
        # Base Layout
        self.main_layout = QtWidgets.QVBoxLayout() if self.vertical else QtWidgets.QHBoxLayout()
        self.margins = QtCore.QMargins(0,0,0,0)
        self.main_layout.setSpacing(6)
        self.main_layout.setContentsMargins(self.margins)
        self.setLayout(self.main_layout)
        # Build Checkboxes
        if self.type == "checkbox":
            for each in self.names:
                self.item_dict[each] = QtWidgets.QCheckBox(each)
                self.main_layout.addWidget(self.item_dict[each])
        elif self.type == "radiobutton":
            for each in self.names:
                self.item_dict[each] = QtWidgets.QRadioButton(each)
                self.main_layout.addWidget(self.item_dict[each])
        elif self.type == "button":
            for each in self.names:
                self.item_dict[each] = QtWidgets.QPushButton(each)
                self.main_layout.addWidget(self.item_dict[each])
        else:
            LOG.error("Invalid value for attribute \"type\". \nValid Options: \"checkbox\", \"radiobutton\", \"button\"")


class BasicWidget(QtWidgets.QWidget):
    def __init__(self, parent=None, layout_type="vertical", spacing=0, margins=[0,0,0,0], h_align="left", v_align="top"):
        '''Creates a widget that acts a base template for other tools to build from.
            Parameters:
                        parent:      The parent widget to attach this widget to. 
                                        Helpful for connecting widget to an application's main window, like Maya. 
                                        Otherwise, leave as None.
                        layout_type: How items are place in the widget's layout.
                                        values: "vertical", "horizontal", "grid"
                        spacing:     Space between other UI components inside this widget.

                        margins:     Border space around all for sides of the widget. 
                                        [left, top, right, bottom]
                        h_align:     Horizontal alignment of items.
                                        values: "left", "center", "right"
                        v_align:     Vertical alignment of items. 
                                        values: "top", "center", "bottom"
        '''
        super(BasicWidget, self).__init__(parent=parent)
        # self.setStyleSheet(STYLESHEET)
        self.layout_type = layout_type
        self.h_align = h_align
        self.v_align = v_align
        self.spacing = spacing
        self.margins = QtCore.QMargins(margins[0], margins[1], margins[2], margins[3])

        # Base Window
        # # Layout Type
        if self.layout_type == "vertical":
            self.layout = QtWidgets.QVBoxLayout()
        elif self.layout_type == "horizontal":
            self.layout = QtWidgets.QHBoxLayout()
        elif self.layout_type == "grid":
            self.layout = QtWidgets.QGridLayout()
        else:
            LOG.error("Invalid Layout Argument: \'{}\'".format(self.layout_type))
        self.setLayout(self.layout)
        # # Layout Alignments:
        # # # Horizontal
        if self.h_align == "left":
            self.layout.setAlignment(QtCore.Qt.AlignLeft)
        elif self.h_align == "center":
            self.layout.setAlignment(QtCore.Qt.AlignHCenter)
        elif self.h_align == "right":
            self.layout.setAlignment(QtCore.Qt.AlignRight)
        else:
            LOG.error("Invalid Horizontal Alignment Argument (\'h_align\'): \'{}\'".format(self.h_align))
        # # # Vertical
        if self.v_align == "top":
            self.layout.setAlignment(QtCore.Qt.AlignTop)
        elif self.v_align == "center":
            self.layout.setAlignment(QtCore.Qt.AlignVCenter)
        elif self.v_align == "bottom":
            self.layout.setAlignment(QtCore.Qt.AlignBottom)
        else:
            LOG.error("Invalid Vertical Alignment Argument (\'v_align\'): \'{}\'".format(self.v_align))
        # # Spacing
        self.layout.setSpacing(self.spacing)
        self.layout.setContentsMargins(self.margins)