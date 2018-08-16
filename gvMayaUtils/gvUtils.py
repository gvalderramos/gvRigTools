from maya import cmds
from types import *


def returnUUID(node=None):

	uuid = []
	if type(node) is ListType:
		for n in node:
			uuids = cmds.ls(node, uuid=True)
			for u in uuids:
				uuid.append(u)
	else:
		uuids = cmds.ls(node, uuid=True)
		for u in uuids:
			uuid.append(u)

	return uuid


def createNode(nodeType='transform', name='transform'):

	node = cmds.createNode(nodeType, name=name)
	uuid = returnUUID(node)
	return (node, uuid)


def returnName(uuid):

	names = []
	if uuid:
		if type(uuid) is ListType:
			shortNames = [cmds.ls(u, shortNames=True) for u in uuid]
			for shortName in shortNames:
				names.append(shortName)
		else:
			shortNames = cmds.ls(uuid, shortNames=True)
			for shortName in shortNames:
				names.append(shortName)

		return names
	else:
		return None


def createTransformer(n='transform', p=(0,0,0), r=(0,0,0)):

	"""
		** create transform node **

		n = name of the node
		p = position (px, py, pz)
		r = rotation (rx, ry, rz)

		return node name and uuid 
	"""

	node, uuid = createNode(nodeType='transform', name=n)

	px, py, pz = p
	cmds.move(px, py, pz)

	rx, ry, rz = r
	cmds.rotate(rx, ry, rz)

	return (node, uuid)


def createPlusMinusAverage(n='plusMinusAverage', operation=0):

	node, uuid = createNode(nodeType='plusMinusAverage', name=n)

	cmds.setAttr("%s.%s" % (node, 'operation'), operation)

	return (node, uuid)


def createMultiplyDivide(n='multiplyDivide', operation=0):
	
	node, uuid = createNode(nodeType='multiplyDivide', name=n)

	cmds.setAttr("%s.%s" % (node, 'operation'), operation)

	return (node, uuid)


def createCondition(n='condition', operation=0):

	node, uuid = createNode(nodeType='condition', name=n)

	cmds.setAttr("%s.%s" % (node, 'operation'), operation)

	return (node, uuid)


def connectOneAttr(obj1, attr1, obj2, attr2):

	if type(obj2) is ListType:
		for o in obj2:
			cmds.connectAttr('%s.%s' % (obj1, attr1), '%s.%s' % (o, attr2), force=True)
	else:
		cmds.connectAttr('%s.%s' % (obj1, attr1), '%s.%s' % (obj2, attr2), force=True)

def connectVecAttrs(obj1="", attr1=['x', 'y', 'z'], obj2="", attr2=['x', 'y', 'z']):

	if type(obj2) is ListType:
		for o in obj2:
			for i in range(len(attr1)):
				cmds.connectAttr('%s.%s' % (obj1, attr1[i]), '%s.%s' % (o, attr2[i]), force=True)
	else:
		for i in range(len(attr1)):
			cmds.connectAttr('%s.%s' % (obj1, attr1[i]), '%s.%s' % (obj2, attr2[i]), force=True)


def create_parent(list=[]):
	for i in range(len(list)):
		if i+1 < len(list):
			cmds.parent(list[i+1], list[i])

def createFkCtrls(locs=[], prefix='', createJoints=True):

	if createJoints:
		jntList = []
		
		c = 1
		for loc in locs:
			cmds.select(clear=True)
			jnt = cmds.joint(n='{}_{:02d}_Jnt'.format(prefix, c))
			jntList.append(jnt)
			cmds.delete(cmds.parentConstraint(loc, jnt))
			cmds.makeIdentity(jnt, apply=True, t=True, r=True, s=True, n=False, pn=True)
			c += 1
		c = 1

		create_parent(jntList)
	else:
		jntList=locs

	ctrls = []
	for i in range(len(jntList)):
		ctrl = cmds.curve(n='{}_{:02d}_Ctrl'.format(prefix, i+1), 
						  d=1, 
						  p=[(-2, 0, 0), 
							 (-1, 0,-1),
							 ( 1, 0,-1),
							 ( 2, 0, 0),
							 ( 1, 0, 1),
							 (-1, 0, 1),
							 (-2, 0, 0)])
		g = cmds.group(ctrl, n='{}_{:02d}_Grp'.format(prefix, i+1))
		g_zero = cmds.group(g, n='{}_{:02d}_Grp_Zero'.format(prefix, i+1))
		ctrls.append((g_zero, g, ctrl))
		cmds.delete(cmds.parentConstraint(jntList[i], g_zero))
		cmds.parentConstraint(ctrl, jntList[i])

	for i in range(len(ctrls)):
		if i+1 < range(len(ctrls)):
			g_zero, g, c = ctrls[i]
			g_zero_p1, g_p1, c_p1 = ctrls[i+1]
			cmds.parent(g_zero_p1, c)