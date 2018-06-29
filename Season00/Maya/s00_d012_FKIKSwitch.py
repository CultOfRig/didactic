from maya.api import _OpenMaya_py2 as om2

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


mobTuple = tuple(iterSelection())
if len(mobTuple) >= 2:
    if mobTuple[0] is not None:
        srtWMtx = om2.MTransformationMatrix(wMtxFromMob(mobTuple[0]))
        srtWMtx.rotateBy(getMRotFromNodeOutput(mobTuple[1]), om2.MSpace.kWorld)