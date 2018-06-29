from maya.api import _OpenMaya_py2 as om2 # helps autocompletion along in most IDEs


def iterSelection():
    """
    generator style iterator over current Maya active selection
    :return: [MObject) an MObject for each item in the selection
    """
    sel = om2.MGlobal.getActiveSelectionList()
    for i in xrange(sel.length()):
        yield sel.getDependNode(i)


def removeCallbacksFromNode(node_mob):
    """
    :param node_mob: [MObject] the node to remove all node callbacks from 
    :return: [int] number of callbacks removed
    """
    cbs = om2.MMessage.nodeCallbacks(node_mob)
    for eachCB in cbs:
        om2.MMessage.removeCallback(eachCB)
    len(cbs)


def translationPlugsFromAnyPlug(plug):
    """
    :param plug: [MPlug] plug on a node to retrieve translation related plugs from
    :return: [tuple(MPlug)] tuple of compound translate plug,
                            and three axes translate plugs
    """
    node = plug.node()
    if not node.hasFn(om2.MFn.kTransform): # this should exclude nodes without translate plugs
        return
    mfn_dep = om2.MFnDependencyNode(node)
    pNames = ('translate', 'tx', 'ty', 'tz')
    return tuple([mfn_dep.findPlug(eachName, False) for eachName in pNames])


def msgConnectedPlugs(plug):
    """
    :param plug: [MPlug] plug on a node owning message plug
                         we wish to retrieve all destination plugs from
    :return: [tuple(MPlug)] all plugs on other nodes receiving a message connection
                            coming from the one owning the argument plug
    """
    mfn_dep = om2.MFnDependencyNode(plug.node())
    msgPlug = mfn_dep.findPlug('message', False)
    return tuple([om2.MPlug(otherP) for otherP in msgPlug.destinations()])


def almostEqual(a, b, rel_tol=1e-09, abs_tol=0.0):
    """
    Lifted from pre 3.5 isclose() implementation,
    floating point error tolerant comparison
    :param a: [float] first number in comparison
    :param b: [float] second number in comparison
    :param rel_tol:  [float] relative tolerance in comparison
    :param abs_tol:  [float] absolute tolerance in case of relative tolerance issues
    :return: [bool] args are equal or not
    """
    return abs(a-b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol)


def cb(msg, plug1, plug2, payload):
    if msg != 2056: #check most common case first and return unless it's
        return      # an attribute edit type of callback

    srcTranslationPlugs = translationPlugsFromAnyPlug(plug1)
    if not len(srcTranslationPlugs):
        return

    # trim out the first plug, the translate compound, and only work on the triplet xyz
    values = [p.asFloat() for p in srcTranslationPlugs[1:4]]

    for eachDestPlug in msgConnectedPlugs(plug1): # all receiving plugs
        destTranslationPlugs = translationPlugsFromAnyPlug(eachDestPlug)[1:4]
        for i, p in enumerate(destTranslationPlugs):
            if almostEqual(p.asFloat(), values[i]):
                continue
            p.setFloat(values[i])


for eachMob in iterSelection():
    removeCallbacksFromNode(eachMob)
    om2.MNodeMessage.addAttributeChangedCallback(eachMob, cb)
