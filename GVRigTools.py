from maya import OpenMayaUI as omui
import maya.cmds as cmds
import pymel.core as pm
from functools import partial
import os
from types import *

from Qt.QtCore import *
from Qt.QtGui import *
from Qt.QtWidgets import *
from Qt import __version__
from shiboken2 import wrapInstance

import re
import string
from itertools import combinations_with_replacement as cwr

import logging

logging.basicConfig()

logger = logging.getLogger('GVRigTools')

logger.setLevel(logging.DEBUG)

"""
    ###     GV RIG TOOLS V102               ###
    ###     Dev by: GABRIEL VALDERRAMOS     ###
    ###     gabrielvalderramos@gmail.com    ###
"""


def get_main_window():
    """
        ###  Cria um instance da janela do maya para o QWidget fique sempre acima da janela  ###
    """
    mayaMainWindowPtr = omui.MQtUtil.mainWindow()
    return wrapInstance(long(mayaMainWindowPtr), QWidget)

def getDock(name='GVRigTools_Window'):
    """
    This function creates a dock with the given name.
    It's an example of how we can mix Maya's UI elements with Qt elements
    Args:
        name: The name of the dock to create

    Returns:
        QtWidget.QWidget: The dock's widget
    """
    # First lets delete any conflicting docks
    deleteDock(name)
    # Then we create a workspaceControl dock using Maya's UI tools
    # This gives us back the name of the dock created
    ctrl = pm.workspaceControl(name, dockToMainWindow=('left', 1), label="GV Rigging Tools")

    # We can use the OpenMayaUI API to get the actual Qt widget associated with the name
    qtCtrl = omui.MQtUtil_findControl(ctrl)

    # Finally we use wrapInstance to convert it to something Python can understand, in this case a QWidget
    ptr = wrapInstance(long(qtCtrl), QWidget)

    # And we return that QWidget back to whoever wants it.
    return ptr


def deleteDock(name='GVRigTools_Window'):
    """
    A simple function to delete the given dock
    Args:
        name: the name of the dock
    """
    # We use the workspaceControl to see if the dock exists
    if pm.workspaceControl(name, query=True, exists=True):
        # If it does we delete it
        pm.deleteUI(name)

def getMayaMainWindow():
    """
    Since Maya is Qt, we can parent our UIs to it.
    This means that we don't have to manage our UI and can leave it to Maya.

    Returns:
        QtWidgets.QMainWindow: The Maya MainWindow
    """
    # We use the OpenMayaUI API to get a reference to Maya's MainWindow
    win = omui.MQtUtil_mainWindow()
    # Then we can use the wrapInstance method to convert it to something python can understand
    # In this case, we're converting it to a QMainWindow
    ptr = wrapInstance(long(win), QMainWindow)
    # Finally we return this to whoever wants it
    return ptr

class RigToolsUI(QWidget):

    """
        ###  Class QWidget  ###
    """

    def __init__(self, dock=True, *args, **kwargs):

        if dock:
            parent = getDock()
        else:
            deleteDock()
            try:
                pm.deleteUI('GVRigTools_Window')
            except:
                logger.debug('No previous UI exists')

            parent = QDialog(parent=getMayaMainWindow())
            parent.setObjectName('GVRigTools_Window')
            parent.setWindowTitle('GV Rigging Tools')

            parent.setWindowFlags(Qt.Window)

            dlgLayout = QVBoxLayout(parent)

        super(RigToolsUI, self).__init__(parent=parent)

        # Set window geometry
        screenShape = QDesktopWidget().screenGeometry()
        screenWidth = screenShape.width()
        screenHeight = screenShape.height()
        winWidth = 500
        winHeight = 400
        parent.setGeometry((screenWidth/2)-(winWidth/2), (screenHeight/2)-(winHeight/2), winWidth, winHeight)

        # lista de meshs para aplicar o skin
        self.sourceMesh = []
        self.targetMesh = []

        # initialize
        self.initUI()

        self.parent().layout().addWidget(self)

        if not dock:
            parent.show()

    def initUI(self):
        '''
            Build UI
        '''
        # layout base
        layout = QVBoxLayout(self)

        # groups box para alocar as tools
        groupBox = QGroupBox('Renamer')
        groupColorPicker = QGroupBox('Color Override')
        groupCopySkin = QGroupBox('Copy Skin')

        # adicao dos groupbox no layout base
        layout.addWidget(groupBox)
        layout.addWidget(groupColorPicker)
        layout.addWidget(groupCopySkin)

        # caixa de texto para renomear os objetos
        self.text_field_rename = QLineEdit()
        QWidget.setToolTipDuration(self.text_field_rename, 0.01)
        QWidget.setToolTip(self.text_field_rename,
                           "Caso queira uma sequencia numerica, digite a quantidade de '#' desejada."
                           "\nCaso queira uma sequencia de letras, digite a quantidade de '@' desejada.")

        # botao para renomear
        rename_btn = QPushButton('Rename Objects')
        rename_btn.clicked.connect(self.renameBtn)

        # Adicao do botao e da caixa de texto no groupBox
        vbox_renamer_group_layout = QHBoxLayout()
        vbox_renamer_group_layout.addWidget(self.text_field_rename)
        vbox_renamer_group_layout.addWidget(rename_btn)
        groupBox.setLayout(vbox_renamer_group_layout)

        # Botoes de override color
        colorBtn = QPushButton('Set Color Override', self)
        colorBtn.clicked.connect(self.set_color)
        QWidget.setToolTip(colorBtn, "Selecione seu(s) controle(s) e clique para escolher a cor desejada")
        removeColorBtn = QPushButton('Remove Color Override')
        QWidget.setToolTip(removeColorBtn, "Remove todos os override de cor")
        removeColorBtn.clicked.connect(self.removeOverride)

        vbox_colorPicker_group_layout = QHBoxLayout()
        vbox_colorPicker_group_layout.addWidget(colorBtn)
        vbox_colorPicker_group_layout.addWidget(removeColorBtn)
        groupColorPicker.setLayout(vbox_colorPicker_group_layout)

        # lista de sources do copy skin

        sourceSkinListWidget = QWidget()
        sourceSkinListLayout = QVBoxLayout(sourceSkinListWidget)
        skinListWidget = QWidget()
        skinListLayout = QHBoxLayout(skinListWidget)

        skinListLayout.addWidget(sourceSkinListWidget)

        size = 30
        self.sourceSkinList = QListWidget()
        sourceSkinListLayout.addWidget(self.sourceSkinList)
        # We set the icon size of this list
        self.sourceSkinList.setIconSize(QSize(size, size))
        # then we set it to adjust its position when we resize the window
        self.sourceSkinList.setResizeMode(QListWidget.Adjust)
        # Finally we set the grid size to be just a little larger than our icons to store our text label too
        self.sourceSkinList.setGridSize(QSize(size+12, size+12))

        self.sourceSkinBtn = QPushButton('Source Meshs')
        QWidget.setToolTip(self.sourceSkinBtn, "Selecione as meshs que voce gostaria de copiar o skin")
        self.sourceSkinBtn.clicked.connect(partial(self.addItensList, self.sourceSkinList, self.sourceMesh))
        sourceSkinListLayout.addWidget(self.sourceSkinBtn)

        # button para transferir o skin de uma lista para outra

        copySkinBtnWidget = QWidget()
        copyBtnLayout = QVBoxLayout(copySkinBtnWidget)
        skinListLayout.addWidget(copySkinBtnWidget)
        self.copySkinBtn = QPushButton('>>>')
        QWidget.setToolTip(self.copySkinBtn, "Copy Skin")
        self.copySkinBtn.clicked.connect(self.funcCopySkinBtn)
        copyBtnLayout.addWidget(self.copySkinBtn)

        # lista de target do copy skin

        targetListWidget = QWidget()
        targetSkinListLayout = QVBoxLayout(targetListWidget)
        skinListLayout.addWidget(targetListWidget)

        self.targetList = QListWidget()
        # We set the icon size of this list
        self.targetList.setIconSize(QSize(size, size))
        # then we set it to adjust its position when we resize the window
        self.targetList.setResizeMode(QListWidget.Adjust)
        # Finally we set the grid size to be just a little larger than our icons to store our text label too
        self.targetList.setGridSize(QSize(size+12, size+12))
        targetSkinListLayout.addWidget(self.targetList)

        self.targetSkinBtn = QPushButton('Target Meshs')
        QWidget.setToolTip(self.targetSkinBtn, "Selecione as meshs que voce gostaria de colar o skin")
        self.targetSkinBtn.clicked.connect(partial(self.addItensList, self.targetList, self.targetMesh))
        targetSkinListLayout.addWidget(self.targetSkinBtn)

        vbox_CopySkin_group_layout = QVBoxLayout()
        vbox_CopySkin_group_layout.addWidget(skinListWidget)
        groupCopySkin.setLayout(vbox_CopySkin_group_layout)


    def removeOverride(self):
        """
            ###  Remove o overrideColor  ###
        """
        sl = cmds.ls(sl=True, l=True)

        if sl:
            for i in range(len(sl)):
                shapes = cmds.listRelatives(sl[i], shapes=True)
                for shape in shapes:
                    cmds.setAttr(shape + '.overrideEnabled', 0)
        else:
            cmds.warning("Selecione antes seu(s) controle(s)")

    def set_color(self):
        """
            ###  Chama a funcao do color picker  ###
        """
        openColorDialog(self)

    def renameBtn(self):
        """
            ###  Chama a funcao renomear objetos  ###
        """
        newName = self.text_field_rename.text()
        renamer(self, newName)

    def addItensList(self, listWidgetObject, listMesh):
        """
            ###  adiciona os itens selecionados na lista especifica ###
        """
        sl = cmds.ls(sl=True, l=True)
        base_dir = os.path.dirname(__file__)+'/icons'


        objs_accepted = ['mesh', 'nurbsSurface', 'nurbsCurve']

        meshs = []
        listWidgetObject.clear()

        for i in range(len(sl)):
            shapes = cmds.listRelatives(sl[i], shapes=True, noIntermediate=True, fullPath=True)
            if shapes:
                for shape in shapes:
                    objType = cmds.objectType( shape )
                    if str(objType) == objs_accepted[0] and not sl[i] in meshs:
                        meshs.append(sl[i])
                        geo_icon = QIcon(base_dir+'/geo_icon.png')
                        listMesh.append(sl[i])
                        item = QListWidgetItem(geo_icon, sl[i])
                        listWidgetObject.addItem(item)
                    if str(objType) == objs_accepted[1] and not sl[i] in meshs:
                        meshs.append(sl[i])
                        geo_icon = QIcon(base_dir+'/surface_icon.png')
                        listMesh.append(sl[i])
                        item = QListWidgetItem(geo_icon, sl[i])
                        listWidgetObject.addItem(item)
                    if str(objType) == objs_accepted[2] and not sl[i] in meshs:
                        meshs.append(sl[i])
                        geo_icon = QIcon(base_dir+'/curve_icon.png')
                        listMesh.append(sl[i])
                        item = QListWidgetItem(geo_icon, sl[i])
                        listWidgetObject.addItem(item)
        print listMesh

    def funcCopySkinBtn(self):

        """
            ###  chama a funcao para copiar o skin de uma lista para a outra  ###
        """

        sourceItems = [str(self.sourceSkinList.item(i).text()) for i in range(self.sourceSkinList.count())]
        targetItems = [str(self.targetList.item(i).text()) for i in range(self.targetList.count())]

        if type(targetItems) is ListType:
            for targetItems in targetItems:
                copySkin(sourceItems, targetItems)
        else:
            copySkin(sourceItems, targetItems)


def openColorDialog(self):
    """
        ###  Abre o color picker e seta o override color  ###
    """
    sl = cmds.ls(sl=True)

    if sl:
        color = QColorDialog.getColor()
        if color.isValid():
            rgba = color.getRgbF()

            for i in range(len(sl)):
                shapes = cmds.listRelatives(sl[i], shapes=True)
                for shape in shapes:
                    cmds.setAttr(shape + '.overrideEnabled', 1)
                    cmds.setAttr(shape + '.overrideRGBColors', 1)
                    cmds.setAttr(shape + '.overrideColorRGB', rgba[0], rgba[1], rgba[2])
        else:
            return
    else:
        cmds.warning("Selecione antes seu(s) controle(s)")


def gen_letters(self, length=2):
    """
        ###  Funcao que gera uma sequencia alfabetica de letras,
        # como por exemplo AAA, AAB, AAC...  ###
    """
    # lista com todas as letras
    alphabet = string.ascii_uppercase
    # Cria uma lista com todas as combinacoes de acordo com o tamanho 'length'
    letters = ["".join(comb) for comb in cwr(alphabet, length)]
    for letter in letters:
        # retorna sob demanda os valores
        yield letter


def renamer(self, newName=""):
    """
        ###  Funcao para renomear os objetos  ###
    """
    sl = cmds.ls(sl=True)
    letters = []
    prefix = None
    suffix = None

    # verifica se o simbolo # esta presente no nome, se estiver, cria uma lista numerica
    if re.search("#", newName) and not re.search("@", newName):
        zeros = [l for l in newName if l == "#"]
        zeros = len(zeros)

        prefix = newName.split('#')[0]
        suffix = newName.split('#')[-1]
    # verifica se o simbolo @ esta presente no nome, cria uma lista alfabetica
    elif re.search("@", newName) and not re.search("#", newName):
        # verifica quantos @s tem no nome
        zeros = [l for l in newName if l == "@"]
        zeros = len(zeros)

        # cria o prefixo e o sufixo do nome
        prefix = newName.split('@')[0]
        suffix = newName.split('@')[-1]

        quant = len(sl) # quantidade de objetos
        letter = gen_letters(self, zeros) # chama a funcao que cria uma lista alfabetica
                                          # com o length de acordo com a quantidade de @s
        # looping para adicionar a sequencia alfabetica no nome
        while True:
            try:
                if quant > 0:
                    letters.append(letter.next())
                    quant = quant - 1
                else:
                    break
            except:
                letter = gen_letters(self, zeros)
                if quant > 0:
                    letters.append(letter.next())
                    quant = quant - 1
                else:
                    break
    # previne que o usuario coloque # e @
    elif re.search("#", newName) and re.search("@", newName):
        cmds.warning("digite exclusivamente '#' ou '@'")
        return
    # se o usuario nao quiser colocar uma sequencia numerica ou alfabetica
    elif not re.search("#", newName) and not re.search("@", newName):
        prefix = newName
        suffix = ""
        zeros = 0

    # Finalmente soma-se o prefixo, como numero/letra e o sufixo
    if sl:
        for mesh in range(len(sl)):
            if suffix:
                if not letters:
                    cmds.rename(sl[mesh], prefix + str(mesh + 1).zfill(zeros) + suffix)
                else:
                    cmds.rename(sl[mesh], prefix + str(letters[mesh]) + suffix)
            else:
                if not letters:
                    cmds.rename(sl[mesh], prefix + str(mesh + 1).zfill(zeros))
                else:
                    cmds.rename(sl[mesh], prefix + str(letters[mesh]))
    else:
        raise RuntimeError("Select your mesh")


def copySkin(sources, target):

    """
        ### Copia o skin de varias ou de apenas uma mesh para outra mesh ###

        sources = Lista com todas as meshs que ira copiar
        target = Objeto final que ira ser 'colado' o skin
    """

    sourceShapes = shapesQuery(sources)
    targetShapes = shapesQuery(target)

    sourceSkinClusters = skinClusterList(sourceShapes)
    targetSkinClusters = skinClusterList(targetShapes)

    print sourceSkinClusters
    print targetSkinClusters

    if targetSkinClusters:
        cmds.delete(targetSkinClusters)

    influences = [ cmds.skinCluster(skinCl, query=True, inf=True) for skinCl in sourceSkinClusters ]
    jnts = [ jnt for i in influences for jnt in i]

    if not jnts:
        print influences, jnts
        cmds.error("Nao foi encontrado joints na mesh target")
        return

    print jnts, target
    cmds.skinCluster(jnts, target, tsb=1, ibp=1)

    cmds.select(clear=True)
    for source in sources:
        cmds.select(source, add=True)
    cmds.select(target, add=True)
    cmds.copySkinWeights(nm=1,sa="closestPoint", ia="closestJoint")

def shapesQuery(selection):
    """
        ### retorna uma lista com todos os shapes de uma selecao ####
    """
    if type(selection) is ListType:
        shapes = [cmds.listRelatives(s, shapes=True, fullPath=True, noIntermediate=True) for s in selection]
    else:
        shapes = cmds.listRelatives(selection, shapes=True, fullPath=True, noIntermediate=True)

    print shapes
    return shapes

def skinClusterList(shapes):
    """
        ### retorna uma lista com os skinClusters Node ####
    """
    skinClusters = []
    for obj in shapes:
        if type(obj) is ListType:
            for shape in obj:
                if not cmds.listConnections(shape, type='skinCluster') == None:
                    skinClusters.append(cmds.listConnections(shape, type='skinCluster'))
        else:
            if not cmds.listConnections(obj, type='skinCluster') == None:
                    skinClusters.append(cmds.listConnections(obj, type='skinCluster'))

    skinClusters = [ shape for obj in skinClusters for shape in obj ]

    return skinClusters

x = RigToolsUI()
