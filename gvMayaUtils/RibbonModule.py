from maya import cmds
import maya.mel as mel

def create_joints(quant=0, namePrefix = 'jnt', nameSuffix = 'Jnt', endName = (True, 'JEnd'), selection=False):

    # create joints basead in selection
    if not selection:
        cmds.select(clear=True)

    # creating new joints
    jnts = []
    endNameBool, JntEnd = endName
    for i in range(quant):
        if i == (quant -1):
            jnts.append(cmds.joint(name="{}_{}".format(namePrefix, JntEnd)))
        else:
            jnts.append(cmds.joint(name="{}_{:02d}_{}".format(namePrefix, i+1, nameSuffix)))

    return jnts

def get_jnt_position(locs = (), joint_list=[], edit=True, edit_axis=(0,1,0)):

    p = []
    locA, locB = locs
    locAPos = cmds.xform(locA, matrix=True, query=True)[-4:-1]
    locBPos = cmds.xform(locB, matrix=True, query=True)[-4:-1]

    res_list = []
    for i in range(3):
        res_list.append((locBPos[i]-locAPos[i])**2)
        if i == 2:
            result = res_list[0]+res_list[1]+res_list[2]
            result = result ** (0.5)

    quant_jnt = len(joint_list) - 1
    if quant_jnt:
        jnt_p = result / quant_jnt
        if edit:
            for i in range(1,len(joint_list)):
                x, y, z = edit_axis
                jnt_x = jnt_p * x
                jnt_y = jnt_p * y
                jnt_z = jnt_p * z
                cmds.setAttr('%s.%s' % (joint_list[i], 'tx'), jnt_x)
                cmds.setAttr('%s.%s' % (joint_list[i], 'ty'), jnt_y)
                cmds.setAttr('%s.%s' % (joint_list[i], 'tz'), jnt_z)
        return jnt_p

def create_curve(curve_name='curve', d=1, joint_list=[], edit=False, curve='curve', edit_axis=(0,1,0)):

    if edit:
        if curve:
            position = []
            for i in range(len(joint_list)):
                jnt_p = cmds.xform(joint_list[i], ws=True, matrix=True, query=True)[-4:-1]
                mel.eval('move %s %s %s -xc edge -xn %s.cv[%s];' % (jnt_p[0], jnt_p[1], jnt_p[2], curve_name, i))

            cv = curve

    else:
        position = []
        for jnt in joint_list:
            jnt_p = cmds.xform(jnt, ws=True, matrix=True, query=True)[-4:-1]
            position += [(jnt_p[0], jnt_p[1], jnt_p[2])]

        cv = cmds.curve(name=curve_name, d=d, p=position)

    return cv

def create_ik_solver(joint_list=[], curve_name=None):

    ik = cmds.ikHandle(startJoint  = joint_list[0],
                       endEffector = joint_list[-1],
                       curve       = curve_name,
                       createCurve = False,
                       rootOnCurve = True,
                       solver      = 'ikSplineSolver',
                       parentCurve = False)

    return ik

def edit_ik(joint_list, curve_name):
    print joint_list
    get_jnt_position(locs=('ctrl01_TEMP', 'ctrl02_TEMP'), joint_list=joint_list, edit=True, edit_axis=(0,1,0))
    create_curve(curve_name=curve_name, d=1, joint_list=joint_list, edit=True, curve=curve_name, edit_axis=(0,1,0))
