from maya import cmds
from types import *

import gvUtils
reload(gvUtils)

from gvUtils import *


class gvPoseReader(object):
	
	def __init__(self, target_name=None, base_name=None, pose_name=None):
		
		if not target_name:
			target_name = 'Target'
		if not base_name:
			base_name = 'Base'
		if not pose_name:
			pose_name = 'Pose'

		self.targetName = target_name
		self.baseName 	= base_name
		self.poseName	= pose_name


	def create_transformers(self):

		self.target, self.targetUUID = createTransformer(n=self.targetName+'_Grp', p=(0,4,0), r=(0,0,0))
		self.base  , self.baseUUID   = createTransformer(n=self.baseName+'_Grp'  , p=(0,0,0), r=(0,0,0))
		self.pose  , self.poseUUID   = createTransformer(n=self.poseName+'_Grp'  , p=(4,4,0), r=(0,0,0))

		cmds.addAttr(self.base, longName='coneAngle', keyable=True)

		cmds.setAttr("%s.%s" % (self.base, 'coneAngle'), 90)


	def create_decomposeMatrix(self):
		
		self.targetMatrix, self.targetMatrixUUID   = createNode(nodeType = 'decomposeMatrix', name=self.targetName+'_Mtx')
		self.baseMatrix  , self.baseMatrixUUID     = createNode(nodeType = 'decomposeMatrix', name=self.baseName  +'_Mtx')
		self.poseMatrix  , self.poseMatrixUUID     = createNode(nodeType = 'decomposeMatrix', name=self.poseName  +'_Mtx')

	
	def create_multDoubleLinear(self):
		
		self.halfConeAngle, self.halfConeAngleUUID = createNode(nodeType = 'multDoubleLinear', name=self.baseName +'_halfConeAngle_Mdl')

		cmds.setAttr('%s.%s' % (self.halfConeAngle, "input2"), 0.5)


	def create_plusMinus(self):

		self.targetVec     , self.targetVecUUID   = createPlusMinusAverage(n=self.targetName+'TargetVec_Pma', operation=2)
		self.currentPoseVec, self.currentVecUUID  = createPlusMinusAverage(n=self.poseName+'CurrentPoseVec_Pma', operation=2)

		self.resultValue   , self.resultValueUUID = createPlusMinusAverage(n=self.baseName+'_ResultValue_Pma', operation=3)
		
		cmds.setAttr('%s.%s' % (self.resultValue, 'input1D[0]'), 1)

	def create_angleBetween(self):

		self.angle, self.angleUUID = createNode(nodeType = 'angleBetween', name=self.targetName+'_Angle_ab')


	def create_multiplyDivide(self):
		
		self.ratioAngle, self.ratioAngleUUID = createMultiplyDivide(n=self.baseName+'_Md', operation=2)


	def create_condition(self):
	
		self.outAngle  , self.outAngleUUID   = createCondition(n=self.baseName+'_Cd', operation=5)

		cmds.setAttr('%s.%s' % (self.outAngle, 'secondTerm'), 1)


	def create_nodes(self):

		self.create_transformers()	
		self.create_decomposeMatrix()
		self.create_multDoubleLinear()
		self.create_plusMinus()
		self.create_angleBetween()
		self.create_multiplyDivide()
		self.create_condition()


	def config_poseReader(self):
		
		connectOneAttr(obj1=self.target, attr1='worldMatrix', obj2=self.targetMatrix, attr2='inputMatrix')

		connectOneAttr(obj1=self.base, attr1='worldMatrix', obj2=self.baseMatrix, attr2='inputMatrix')
		connectOneAttr(obj1=self.base, attr1='coneAngle', obj2=self.halfConeAngle, attr2='input1')

		connectOneAttr(obj1=self.pose, attr1='worldMatrix', obj2=self.poseMatrix, attr2='inputMatrix')

		connectVecAttrs(obj1  = self.poseMatrix, 
						attr1 = ['outputTranslateX', 'outputTranslateY', 'outputTranslateZ'],
						obj2  = self.currentPoseVec,
						attr2 = ['input3D[0].input3Dx', 'input3D[0].input3Dy', 'input3D[0].input3Dz'])		

		connectVecAttrs(obj1  = self.targetMatrix, 
						attr1 = ['outputTranslateX', 'outputTranslateY', 'outputTranslateZ'],
						obj2  = self.targetVec,
						attr2 = ['input3D[0].input3Dx', 'input3D[0].input3Dy', 'input3D[0].input3Dz'])

		connectVecAttrs(obj1  = self.baseMatrix,
						attr1 = ['outputTranslateX', 'outputTranslateY', 'outputTranslateZ'],
						obj2  = [self.targetVec, self.currentPoseVec],
						attr2 = ['input3D[1].input3Dx', 'input3D[1].input3Dy', 'input3D[1].input3Dz'])
		
		connectVecAttrs(obj1  = self.targetVec,
						attr1 = ['output3Dx', 'output3Dy', 'output3Dz'],
						obj2  = self.angle,
						attr2 = ['vector1X', 'vector1Y', 'vector1Z'])

		connectVecAttrs(obj1  = self.currentPoseVec,
						attr1 = ['output3Dx', 'output3Dy', 'output3Dz'],
						obj2  = self.angle,
						attr2 = ['vector2X', 'vector2Y', 'vector2Z'])

		connectOneAttr(obj1=self.angle, attr1='angle', obj2=self.ratioAngle, attr2='input1X')
		
		connectOneAttr(obj1=self.halfConeAngle, attr1='output', obj2=self.ratioAngle, attr2='input2X')

		connectOneAttr(obj1=self.ratioAngle, attr1='outputX', obj2=self.outAngle, attr2='colorIfTrue.colorIfTrueR')
		connectOneAttr(obj1=self.ratioAngle, attr1='outputX', obj2=self.outAngle, attr2='firstTerm')

		connectOneAttr(obj1=self.outAngle, attr1='outColorR', obj2=self.resultValue, attr2='input1D[1]')
		