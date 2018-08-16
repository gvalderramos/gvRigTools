import pymel.core as pm
from maya import cmds

class MOVEALL(object):
    def __init__(self):

        self.parentGrp, self.renderGrp, self.renderObjs = getMesh()

        if self.renderGrp:
            self.bMax, self.bMin = getBoundingBox(self.renderGrp)

    def createHierarchy(self):
        pm.parent(self.middleGrp.name(), self.rootCtrl.name())
        pm.parent(self.rootGrp.name(), self.masterCtrl.name())
        pm.parent(self.masterGrp.name(), self.globalCtrl.name())

    def configureMiddle(self):
        posM = (0, self.bMax.y / 2, 0)

        pm.move(self.middleGrp, posM)
        parentAndScale(self.middleCtrl, self.renderGrp)

    def configureAllGrp(self):
        self.allGrp = createTransform('all_grp')
        pm.parent(self.globalGrp, self.allGrp)
        pm.parent(self.renderGrp, self.allGrp)

    def verifyMeshObjs(self):
        if pm.objExists('mesh_set'):
            meshsInSet = pm.sets('mesh_set', nodesOnly=True, query=True)
            for mesh in self.renderObjs:
                if not mesh in meshsInSet:
                    pm.sets('mesh_set', addElement=mesh)
        else:
            pm.sets(self.renderObjs, name='mesh_set')

    def createLattice(self, d=(6,6,6), n='deformerLattice'):

        if self.renderObjs:
            self.lttc = pm.lattice(self.renderObjs,
                                   divisions=d,
                                   objectCentered=True,
                                   ldv=d, ol=True, name=n)
            print self.lttc

        self.latticeGrp = createTransform(name='lattice_grp')

        if not pm.objExists('data_grp'):
            self.dataGrp = createTransform('data_grp')

        pm.parent(self.latticeGrp, self.dataGrp)
        pm.parent(self.dataGrp, self.allGrp)
        pm.setAttr('%s.visibility' % self.dataGrp, 0)

        for i in range(1,3): pm.parent(self.lttc[i], self.latticeGrp)

        parentAndScale(ctrl=self.middleCtrl, target=self.latticeGrp)

    def createDeformers(self, lattice=None):

        if not lattice:
            l = self.lttc[1]
        else:
            l = lattice

        self.twistDeformer, self.twistHandle = pm.nonLinear(l, type='twist',
                                                               lowBound=-2,
                                                               highBound=0)
        pm.move(self.twistHandle, (0,0,0))
        pm.rotate(self.twistHandle, (0,0,-180))

        self.squashDeformer, self.squashHandle = pm.nonLinear(l, type='squash',
                                                                 lowBound=0,
                                                                 highBound=2)
        pm.move(self.squashHandle, (0,0,0))

        self.bendDeformerX, self.bendHandleX = pm.nonLinear(l, type='bend',
                                                               curvature=0,
                                                               lowBound=0,
                                                               highBound=2)
        pm.move(self.bendHandleX, (0,0,0))
        pm.rotate(self.bendHandleX, (0,90,0))

        self.bendDeformerZ, self.bendHandleZ = pm.nonLinear(l, type='bend',
                                                               curvature=0,
                                                               lowBound=0,
                                                               highBound=2)
        pm.move(self.bendHandleZ, (0,0,0))

        self.deformerGrp = createTransform('deformer_grp')

        for deformer in [self.twistHandle,
                         self.squashHandle,
                         self.bendHandleX,
                         self.bendHandleZ]:

            pm.parent(deformer, self.deformerGrp)

        parentAndScale(self.middleCtrl, self.deformerGrp)
        pm.parent(self.deformerGrp, '%s|%s' % (self.allGrp, self.dataGrp))

    def createDeformerControl(self, name='deform_ctrl'):
        factor = self.bMax.x/6
        self.deformerCtrl = pm.curve(d=1,
                                     p=[(-1*factor,4*factor,0*factor),
                                        (-1*factor,2*factor,0*factor),
                                        (-2*factor,2*factor,0*factor),
                                        ( 0*factor,0*factor,0*factor),
                                        ( 2*factor,2*factor,0*factor),
                                        ( 1*factor,2*factor,0*factor),
                                        ( 1*factor,4*factor,0*factor)],
                                        name=name)

        self.deformerCtrlGrp = createTransform(name+'_grp')
        pm.parent(self.deformerCtrl, self.deformerCtrlGrp)

        pm.move(self.deformerCtrlGrp, (0,self.bMax.y, 0))

        pm.parent(self.deformerCtrlGrp, self.middleCtrl.name())

        pm.setAttr("%s.rx" % self.deformerCtrl, lock=True, keyable=False, channelBox=False)
        pm.setAttr("%s.rz" % self.deformerCtrl, lock=True, keyable=False, channelBox=False)
        pm.setAttr("%s.sx" % self.deformerCtrl, lock=True, keyable=False, channelBox=False)
        pm.setAttr("%s.sy" % self.deformerCtrl, lock=True, keyable=False, channelBox=False)
        pm.setAttr("%s.sz" % self.deformerCtrl, lock=True, keyable=False, channelBox=False)
        pm.setAttr("%s.visibility" % self.deformerCtrl, lock=True, keyable=False, channelBox=False)

        setCtrlColor(transform=self.deformerCtrl, colorid=17)

        pm.addAttr(self.deformerCtrl.fullPath(), longName="deformFactor", at="double3", keyable=True)
        pm.addAttr(self.deformerCtrl.fullPath(), longName="deformFactorX", p="deformFactor", at="double", keyable=True)
        pm.addAttr(self.deformerCtrl.fullPath(), longName="deformFactorY", p="deformFactor", at="double", keyable=True)
        pm.addAttr(self.deformerCtrl.fullPath(), longName="deformFactorZ", p="deformFactor", at="double", keyable=True)
        pm.setAttr(self.deformerCtrl.fullPath()+'.deformFactorX', keyable=False, channelBox=True)
        pm.setAttr(self.deformerCtrl.fullPath()+'.deformFactorY', keyable=False, channelBox=True)
        pm.setAttr(self.deformerCtrl.fullPath()+'.deformFactorZ', keyable=False, channelBox=True)

    def configureDeformers(self, n='deformer_translate_md', factor=10):

        self.deformerMD = pm.createNode('multiplyDivide', name=n)

        pm.connectAttr("%s.translateX" % self.deformerCtrl.name(), '%s.input1X' % n)
        pm.connectAttr("%s.translateY" % self.deformerCtrl.name(), '%s.input1Y' % n)
        pm.connectAttr("%s.translateZ" % self.deformerCtrl.name(), '%s.input1Z' % n)

        pm.connectAttr("%s.deformFactorX" % self.deformerCtrl.name(), '%s.input2X' % n)
        pm.connectAttr("%s.deformFactorY" % self.deformerCtrl.name(), '%s.input2Y' % n)
        pm.connectAttr("%s.deformFactorZ" % self.deformerCtrl.name(), '%s.input2Z' % n)

        pm.connectAttr("%s.outputX" % n, "%s.curvature" % self.bendDeformerZ.nodeName())
        pm.connectAttr("%s.outputY" % n, "%s.factor" % self.squashDeformer.nodeName())
        pm.connectAttr("%s.outputZ" % n, "%s.curvature" % self.bendDeformerX.nodeName())

        pm.setAttr("%s.deformFactorX" % self.deformerCtrl.name(), self.bMax.x*factor)
        pm.setAttr("%s.deformFactorZ" % self.deformerCtrl.name(), (self.bMax.z*factor)*-1)
        pm.setAttr("%s.deformFactorY" % self.deformerCtrl.name(), (self.bMax.y/10))

        pm.connectAttr("%s.rotateY" % self.deformerCtrl.name(), "%s.startAngle" % self.twistDeformer)

    def createUUIDAttr(self):

        root_name_list = [mesh.name() for mesh in self.renderObjs]

        root_shapes_list = [ cmds.listRelatives(mesh, shapes=True, noIntermediate=True)[0] for mesh in root_name_list ]
        root_uuid_list   = [ cmds.ls(shape, uuid=True)[0] for shape in root_shapes_list ]

        for uuid in root_uuid_list:
            shape = cmds.ls(uuid, uuid=True)[0]
            if not cmds.attributeQuery( 'consuladoID', node=shape, exists=True):
                cmds.addAttr(shape, longName='consuladoID', keyable=True, dt="string")
                cmds.setAttr(shape+'.consuladoID', uuid, type="string")
                cmds.setAttr(shape+'.consuladoID', keyable=False, lock=True, channelBox=True)
            else:
                cmds.setAttr(shape+'.consuladoID', lock=False)
                cmds.setAttr(shape+'.consuladoID', uuid, type="string")
                cmds.setAttr(shape+'.consuladoID', keyable=False, lock=True, channelBox=True)

        queryAttr = []
        for uuid in root_uuid_list:
            shape = cmds.ls(uuid, uuid=True)[0]
            if not cmds.attributeQuery( 'consuladoID', node=shape, exists=True):
                queryAttr.append(True)

        return queryAttr

    def createRig(self):
        radius = self.bMax.x+1
        self.globalGrp, self.globalCtrl = createController(grpName = 'global_ctrl_grp',
                                                           ctrlName = 'global_ctrl',
                                                           r = radius+3*(radius/3))
        setCtrlColor(transform=self.globalCtrl, colorid=1)
        self.masterGrp, self.masterCtrl = createController(grpName = 'master_ctrl_grp',
                                                           ctrlName = 'master_ctrl',
                                                           r = radius+2*(radius/3))
        setCtrlColor(transform=self.masterCtrl, colorid=4)
        self.rootGrp, self.rootCtrl     = createController(grpName = 'root_ctrl_grp',
                                                           ctrlName = 'root_ctrl',
                                                           r = radius+(radius/3))
        setCtrlColor(transform=self.rootCtrl, colorid=13)
        self.middleGrp, self.middleCtrl = createController(grpName = 'middle_ctrl_grp',
                                                           ctrlName = 'middle_ctrl',
                                                           r = radius)
        setCtrlColor(transform=self.middleCtrl, colorid=14)
        self.createHierarchy()
        self.configureMiddle()
        self.configureAllGrp()

        self.verifyMeshObjs()
        self.createLattice()

        self.createDeformers()
        self.createDeformerControl()
        self.configureDeformers()

        self.createUUIDAttr()

def setCtrlColor(transform, colorid):

    shapes = pm.listRelatives(transform, shapes=True, noIntermediate=True)
    if shapes:
        for shape in shapes:
            pm.setAttr("%s.overrideEnabled" % shape, 1)
            pm.setAttr("%s.overrideColor" % shape, colorid)

def parentAndScale(ctrl, target):
    pm.parentConstraint(ctrl, target, mo=True)
    pm.scaleConstraint(ctrl, target, mo=True)

def createController(grpName, ctrlName, r):
    grp = createTransform(grpName)
    ctrl = createCurve(name = ctrlName, nr = (0,1,0), r = r)[0]
    pm.parent(ctrl, grp)

    return grp, ctrl

def createTransform(name):
    return pm.createNode('transform', n=name)

def createCurve(name="controller", nr=(0,1,0), r=1):
    return pm.circle(n=name, nr=nr, r=r, ch=False)

def getBoundingBox(mesh):
    bMax = pm.getAttr(mesh.name()+'.boundingBoxMax')
    bMin = pm.getAttr(mesh.name()+'.boundingBoxMin')

    return bMax, bMin

def getTopParent(selection, upperParents):
    for mesh in selection:
        prt = pm.listRelatives(mesh, allParents=True)
        if len(prt) > 0:
            getTopParent(prt, upperParents)
        else:
            upperParents.append(mesh)
    return list(set(upperParents))

def getMesh():
    sl = pm.ls(sl=True)
    if not sl:
        pm.confirmDialog( title='Error', message='Selecione as meshs primeiro para criar o Move All', button=["OK"])
        pm.error("Selecione as meshs para criar o moveall")
        return
    else:
        topParent = []
        p = getTopParent(sl, topParent)
        grp = pm.group(p, n='render_grp')
        return p, grp, sl
