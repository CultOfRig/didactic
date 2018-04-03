from maya import cmds as m_cmds
from maya.api import OpenMaya as om2


def iterMobFromActiveSelection():
    """
    Generator iterating the active Maya selection
    :return: `MObject`
    """
    sel = om2.MGlobal.getActiveSelectionList()
    selLength = sel.length()

    for i in xrange(selLength):
        eachMob = sel.getDependNode(i)
        yield eachMob

        selectedContainers = {}


def containerFromNode(mayaNode):
    """
    Inspects a node connection set for standard containered topology and returns
      the owning container if one is found, None otherwise
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


CONTAINER_SUFFIX = '_container'
def iterContainersFromObjectIterator(generator, suffixFilter = CONTAINER_SUFFIX):
    """
    Generator iterating connected containers given an MObject iterator and an optional filter
    The filter will also act as a trim factor to reduce the name of the object,
      this helps since the name of the component shouldn't include the suffix
      describing the object type inspected.
    :param generator: `generator` A Python Generator that yield MObject types
    :param suffixFilter: `str` A string to restrict yield to items with a certain suffix.
                               Can be None, False, or empty if filter is undesirable
    :return: `(str, MObjectHandle)` A tuple containing the name of the container and the
                                      Maya object handle of the container node
    """
    for x in generator():
        container = containerFromNode(x)
        if container is None:
            continue

        k = om2.MFnDependencyNode(container).name()
        if suffixFilter:
            if not k.endswith(suffixFilter):
                continue
            k = k[:-len(suffixFilter)]

        yield k, om2.MObjectHandle(container)


def keyObjectsFromContainer(componentName, containerHandle):
    """
    This takes a component name for some filtering and a container handle and isolates
      the key objects related to it that represent our component interesting items.
    :param componentName: `str` mandatory now, used to compose full name of some exepcted items/paths
    :param containerHandle: `MObjectHandle`
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
    Takes key objects and deletes the guide DAG object in it if present
    :param keyObs: `dict` key objects in a pre-canned dictionary as informed by keyObjectsFromContainer
    :return: `bool` True if the guide was found and deleted, False if one wasn't found
    """
    hasBeenDeleted = False

    if keyObs['guide'] is not None:
        dagPathToGuide = om2.MDagPath.getAPathTo(keyObs['guide'].object()).fullPathName()
        m_cmds.delete(dagPathToGuide)
        hasBeenDeleted = True
    return hasBeenDeleted



TRACKER_PLUG_NAMES = ('origin', 'guided')
def trackerSubplugsFromPlug(plug):
    """
    This takes a well formed plug that is a compound and has two children and forms a dictionary from it
      containing those two sub plugs indexed by their expected names
    :param plug: `MPlug` Compound of two plugs with children named as indicated in preceding constant
    :return: `dict` {origin:MPlug, guided:MPlug}
    """
    assert plug.isCompound, "plug is not compound"
    assert plug.numChildren() == 2, "plug has unexpected number of children"

    childrenChount = plug.numChildren()
    trackedPlugsDict = {TRACKER_PLUG_NAMES[0]: None, TRACKER_PLUG_NAMES[1]: None}
    for j in xrange(childrenChount):
        subPlug = plug.child(j)
        plugKey = subPlug.partialName().rsplit('.', 1)[-1]
        trackedPlugsDict[plugKey] = om2.MPlug().copy(subPlug)

    return trackedPlugsDict



def activePlugsFromTrackerDict(trackerDict):
    retDict = {TRACKER_PLUG_NAMES[0]: None, TRACKER_PLUG_NAMES[1]: None, 'guidedSource': None}
    assert isinstance(trackerDict, dict)
    for k in TRACKER_PLUG_NAMES:
        assert k in trackerDict

    if trackerDict[TRACKER_PLUG_NAMES[0]].isDestination:
        retDict[TRACKER_PLUG_NAMES[0]] = om2.MPlug().copy(trackerDict[TRACKER_PLUG_NAMES[0]].source())

    assert trackerDict[TRACKER_PLUG_NAMES[1]] is not None, "received a None guided plug, this should never happen"
    retDict[TRACKER_PLUG_NAMES[1]] = om2.MPlug().copy(trackerDict[TRACKER_PLUG_NAMES[1]].source())

    guidedPlugSource = om2.MPlug().copy(retDict[TRACKER_PLUG_NAMES[1]].source())
    if not guidedPlugSource.isNull:
        retDict['guidedSource'] = guidedPlugSource

    return retDict


# Parameters indicating what actions we expect to run
DO_SWAP = True
DELETE_DG = False
DELETE_OBJS = False

# main
for compName, mobhaContainer in iterContainersFromObjectIterator(iterMobFromActiveSelection):
    # todo: We rely on some sync between our various iterators hinging around this dictionary.
    # todo: We'll need to double check it.
    keyObs = keyObjectsFromContainer(compName, mobhaContainer)
    toolPanelMobha = keyObs['toolParameters']

    if toolPanelMobha is not None and toolPanelMobha.isValid():
        mob = toolPanelMobha.object()

        mfn_dag = om2.MFnDagNode(mob)


        if DO_SWAP:
            toSwapPlug = mfn_dag.findPlug('toSwap', False)

            elemCount = toSwapPlug.evaluateNumElements()

            toolPanelCouples = [None]*elemCount
            activePlugCouples = [None]*elemCount

            for i in xrange(elemCount):
                # fetching all guide tools plugs first
                elemPlug = toSwapPlug.elementByPhysicalIndex(i)

                trackerPlugsDict = trackerSubplugsFromPlug(elemPlug)
                # todo: replace outer scope doing this job with a map
                toolPanelCouples[i] = trackerPlugsDict

                # going from tracker plugs to active ones
                activePlugsDict = activePlugsFromTrackerDict(trackerPlugsDict)

                doNothing = activePlugsDict['origin'] is None and activePlugsDict['guidedSource'] is None
                disconnect = activePlugsDict['origin'] is None and activePlugsDict['guidedSource'] is not None
                swap = activePlugsDict['origin'] is not None and activePlugsDict['guidedSource'] is not None
                connect = activePlugsDict['origin'] is not None and activePlugsDict['guidedSource'] is None

                if doNothing:
                    pass
                elif disconnect:
                    activeGuidedSource_name = activePlugsDict['guidedSource'].partialName(useFullAttributePath=True,
                                                                                          includeNodeName=True,
                                                                                          useLongNames=True)
                    activeGuided_name= activePlugsDict['guided'].partialName(useFullAttributePath=True,
                                                                             includeNodeName=True,
                                                                             useLongNames=True)
                    trackerOrigin_name= trackerPlugsDict['origin'].partialName(useFullAttributePath=True,
                                                                               includeNodeName=True,
                                                                               useLongNames=True)

                    m_cmds.disconnectAttr(activeGuidedSource_name, activeGuided_name)
                    m_cmds.connectAttr(activeGuidedSource_name, trackerOrigin_name)
                elif connect:
                    activeOriginSource_name = activePlugsDict['origin'].partialName(useFullAttributePath=True,
                                                                                    includeNodeName=True,
                                                                                    useLongNames=True)
                    trackerOrigin_name = trackerPlugsDict['origin'].partialName(useFullAttributePath=True,
                                                                                includeNodeName=True,
                                                                                useLongNames=True)
                    activeGuided_name = activePlugsDict['guided'].partialName(useFullAttributePath=True,
                                                                              includeNodeName=True,
                                                                              useLongNames=True)

                    m_cmds.connectAttr(activeOriginSource_name, activeGuided_name)
                    m_cmds.disconnectAttr(activeOriginSource_name, trackerOrigin_name)
                elif swap:
                    activeOriginSource_name = activePlugsDict['origin'].partialName(useFullAttributePath=True,
                                                                                    includeNodeName=True,
                                                                                    useLongNames=True)
                    trackerOrigin_name = trackerPlugsDict['origin'].partialName(useFullAttributePath=True,
                                                                                includeNodeName=True,
                                                                                useLongNames=True)
                    activeGuided_name = activePlugsDict['guided'].partialName(useFullAttributePath=True,
                                                                              includeNodeName=True,
                                                                              useLongNames=True)
                    activeGuidedSource_name = activePlugsDict['guidedSource'].partialName(useFullAttributePath=True,
                                                                                          includeNodeName=True,
                                                                                          useLongNames=True)
                    m_cmds.connectAttr(activeGuidedSource_name, trackerOrigin_name, force=True)
                    m_cmds.connectAttr(activeOriginSource_name, activeGuided_name, force=True)
                else:
                    # todo: raise meaningful error with sensible message
                    raise RuntimeError("should have never got here!")

        if DELETE_DG:
            # DG deletion part
            toSwapPlug = mfn_dag.findPlug('toDelete', False)
            elemCount = toSwapPlug.evaluateNumElements()

            for i in xrange(elemCount):
                elemPlug = toSwapPlug.elementByPhysicalIndex(i)
                if elemPlug.isDestination:
                    sourceNode = elemPlug.source().node()
                    
                    pathToNode = ''
                    if sourceNode.hasFn(om2.MFn.kDagNode):
                        om2.MDagPath.getAPathTo(sourceNode)
                        pathToNode = om2.MDagPath.getAPathTo(sourceNode).fullPathName()
                    else:
                        pathToNode = om2.MFnDependencyNode(sourceNode).name()
                        
                    if pathToNode:
                        m_cmds.delete(pathToNode)

        if DELETE_OBJS:
            # DAG deletion part
            # todo: check what the heck these keyObs yield
            print keyObs['componentName'], deleteGuideHierarchyFromKeyObjects(keyObs)











