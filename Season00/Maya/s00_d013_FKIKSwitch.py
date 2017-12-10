from maya.api import _OpenMaya_py2 as om2
from maya import cmds
import math

def iterSelection():
    """
    generator style iterator over current Maya active selection
    :return: [MObject) an MObject for each item in the selection
    """
    sel = om2.MGlobal.getActiveSelectionList()
    for i in xrange(sel.length()):
        yield sel.getDependNode(i)


_MAYA_MATRIX_ATTRIBUTE_NAME = 'worldMatrix'
def wMtxFromMob(node_mob):
    """
    finds the world matrix attribute and returns its value in matrix form
    :param node_mob: [MObject] the node to get the world matrix from 
    :return: [MMatrix] the matrix value of the world transform on the argument node
    """
    if not node_mob.hasFn(om2.MFn.kDagNode):
        return None

    mfn_dag = om2.MFnDagNode(node_mob)
    wMtxPlug = mfn_dag.findPlug(_MAYA_MATRIX_ATTRIBUTE_NAME, False)
    elPlug = wMtxPlug.elementByLogicalIndex(0)

    node_mob_attr = elPlug.asMObject()
    mfn_mtxData = om2.MFnMatrixData(node_mob_attr)
    return mfn_mtxData.matrix()


def mtxFromPlugSource(plug):
    """
    takes a plug and retrieves the plug's source plug
      then will try to initialise matrix data from it and return it
      if valid
    :param plug: [MPlug] a plug connected to a matrix type source
    :return: [MMatrix | None]
    """
    if plug.isDestination:
        mtxPlug = plug.source()
        node_mob_attr = mtxPlug.asMObject()
        if node_mob_attr.hasFn(om2.MFn.kMatrixAttribute):
            mfn_mtxData = om2.MFnMatrixData(node_mob_attr)
            return mfn_mtxData.matrix()
    return None


def mPointFromPlugSource(plug):
    """
    similar to mtxFromPlugSource but will retrieve a translate compound source
    :param plug: [MPlug] a plug connected to a translate compound triplet source
    :return: [MPoing | None]
    """
    if plug.isDestination:
        sourcePlug = plug.source()
        if not  sourcePlug.isCompound or not sourcePlug.numChildren() == 3:
            return None
            
        mp = om2.MPoint()
        returnPoint = [False,False,False]
        for i in xrange(sourcePlug.numChildren()):
            realName = sourcePlug.child(i).partialName(includeNodeName = False, useAlias = False)
            if realName == 'tx':
                mp.x = sourcePlug.child(i).asFloat()
                returnPoint[0] = True
            elif realName == 'ty':
                mp.y = sourcePlug.child(i).asFloat()
                returnPoint[1] = True
            elif realName == 'tz':
                mp.z = sourcePlug.child(i).asFloat()
                returnPoint[2] = True
        if all(returnPoint):
            return mp
        return None
    

_MAYA_OUTPUT_ATTRIBUTE_NAME = 'output'
def getMRotFromNodeOutput(node_mob, rotOrder = om2.MEulerRotation.kXYZ):
    """
    finds the angular output of the argument node and returns it
     as a Euler rotation where that angle is the X element
    :param node_mob: [MObject] the node to get the output port from
    :param rotOrder: [int] the factory constant for the desired rotation order
                            the returned Euler rotation should be set to
    :return: [MEulerRotation] the Euler rotation composition where the
                                angular output on the argument node is the X value
    """
    mfn_dep = om2.MFnDependencyNode(node_mob)
    angle = om2.MAngle(0.0)
    if node_mob.hasFn(om2.MFn.kAnimBlend) and mfn_dep.hasAttribute(_MAYA_OUTPUT_ATTRIBUTE_NAME):
        plug = mfn_dep.findPlug(_MAYA_OUTPUT_ATTRIBUTE_NAME, False)
        angle = plug.asMAngle()

    rot = om2.MEulerRotation(angle.asRadians(), 0.0, 0.0, rotOrder)
    return rot


# A dictionary of all attributes we're interested in by name, ready
#   to accept values for each.
attribs = {
           'blendedRotation': None,
           'fk_bfr_mtx': None,
           'ik_bfr_mtx': None,
           'ikPedalOffset': None,
           }


mobTuple = tuple(iterSelection())
if mobTuple:
    mfn_dep = om2.MFnDependencyNode(mobTuple[0])
    plug = om2.MPlug()
    if mfn_dep.hasAttribute("FKIK_switch"):
        plug = mfn_dep.findPlug("FKIK_switch", False)

    if plug.isNull:
        print("invalid selection, no FKIK_switch attribute found on first selected item")
    else:
        for eachPName in attribs.iterkeys():
            plug = mfn_dep.findPlug(eachPName, False)
            attribs[eachPName] = plug

    isValid = True
    for p in attribs.itervalues():
        if p is None:
            isValid = False
            break

    if isValid:
        blendedRot = fk_bfr_mtx = ik_bfr_mtx = ikPedalOffset = None
        blendedRot = attribs.get("blendedRotation").source().asMAngle().asRadians()
        fk_bfr_mtx = mtxFromPlugSource(attribs.get("fk_bfr_mtx"))
        ik_bfr_mtx = mtxFromPlugSource(attribs.get("ik_bfr_mtx"))
        ikPedalOffset = mPointFromPlugSource(attribs.get("ikPedalOffset"))

        projectedLen = ikPedalOffset.y
        z = math.sin(blendedRot) * projectedLen
        y = (1.0-math.cos(blendedRot)) * -projectedLen
else:
    print("invalid selection count, nothing found selected from iterator")

