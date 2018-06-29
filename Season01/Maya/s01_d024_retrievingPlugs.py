from maya import cmds as m_cmds
from maya.api import OpenMaya as om2


def iterMobFromActiveSelection():
    sel = om2.MGlobal.getActiveSelectionList()
    selLength = sel.length()

    for i in xrange(selLength):
        eachMob = sel.getDependNode(i)
        yield eachMob


def containerFromNode(mayaNode):
    """

    :param mayaNode: `MObject` any dependency node in Maya
    :return: `MObject | None` the container object the argument is linked to if there is one
                                otherwise None
    """
    fnDep = om2.MFnDependencyNode(mayaNode)
    plug = fnDep.findPlug("message", False)

    for eachDestPlug in plug.destinations():
        destNode = eachDestPlug.node()
        if not destNode.hasFn(om2.MFn.kHyperLayout):
            continue

        # at this point we're dealing with an interesting node
        #  and we should find if it's connected to a container
        fnDestNode = om2.MFnDependencyNode(destNode)
        layoutMsg = fnDestNode.findPlug("message", False)

        layoutDestinations = layoutMsg.destinations()
        for eachLayoutDestination in layoutDestinations:
            if eachLayoutDestination.node().hasFn(om2.MFn.kContainer):
                return eachLayoutDestination.node()


def keyObjectsFromContainer(containerHandle, componentName):
    """

    :param containerHandle: `MObjectHandle`
    :param componentName: `str` mandatory now, used to compose full name of some exepcted items/paths
    :return: `dict` k,v pairs for interesting objects and their handle, None if unavailable
    """

    mfn_cont = om2.MFnContainerNode(containerHandle.object())
    mobaMembers = mfn_cont.getMembers()

    keyObsDict = {
        'componentName': componentName,
        'control':None,
        'guide':None,
        'deform':None,
        'toolParameters':None,
    }

    for eachMob in mobaMembers:
        if not eachMob.hasFn(om2.MFn.kDagNode):
            continue

        mfn_dag = om2.MFnDagNode(eachMob)

        objectName = mfn_dag.name()

        if objectName == 'control':
            keyObsDict['control'] = om2.MObjectHandle(eachMob)
        elif objectName == 'guide':
            keyObsDict['guide'] = om2.MObjectHandle(eachMob)
        elif objectName == 'control':
            keyObsDict['deform'] = om2.MObjectHandle(eachMob)
        elif objectName == '{}_toolParameters'.format(componentName):
            # todo: the above string composition running every loop is an abomination
            keyObsDict['toolParameters'] = om2.MObjectHandle(eachMob)

    return keyObsDict


def deleteGuideHierarchyFromKeyObjects(keyObs):
    """

    :param keyObs: `dict` key objects in a pre-canned dictionary as informed by keyObjectsFromContainer
    :return: `bool` True if the guide was found and deleted, False if one wasn't found
    """
    hasBeenDeleted = False

    if keyObs['guide'] is not None:
        dagPathToGuide = om2.MDagPath.getAPathTo(keyObs['guide'].object()).fullPathName()
        m_cmds.delete(dagPathToGuide)
        hasBeenDeleted = True
    return hasBeenDeleted



# main

selectedContainers = {}
for x in iterMobFromActiveSelection():
    container = containerFromNode(x)
    if container is None:
        continue

    k = om2.MFnDependencyNode(container).name()
    if k.endswith('_container'):
        k = k[:-len('_container')]

    v = om2.MObjectHandle(container)

    selectedContainers[k] = v


DELETE_OBJS = False
for compName, mobhaContainer in selectedContainers.iteritems():
    keyObs = keyObjectsFromContainer(mobhaContainer, compName)

    if DELETE_OBJS:
        print keyObs['componentName'], deleteGuideHierarchyFromKeyObjects(keyObs)

    toolPanelMobha = keyObs['toolParameters']
    if toolPanelMobha is not None and toolPanelMobha.isValid():
        mob = toolPanelMobha.object()

        mfn_dag = om2.MFnDagNode(mob)
        toSwapPlug = mfn_dag.findPlug('toSwap', False)

        elemCount = toSwapPlug.evaluateNumElements()

        allSwapCouples = [None]*elemCount

        for i in xrange(elemCount):
            elemPlug = toSwapPlug.elementByLogicalIndex(i)
            childrenChount = elemPlug.numChildren()
            subPlugsDict = {'origin':None, 'guided':None}
            for j in xrange(childrenChount):
                subPlug = elemPlug.child(j)
                plugKey = subPlug.partialName().rsplit('.', 1)[-1]
                
                subPlugsDict[plugKey] = om2.MPlug().copy(subPlug)

            allSwapCouples[i] = subPlugsDict

        print allSwapCouples
                



