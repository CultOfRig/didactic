
"""
A Plugin working with Cult of Rig season 1 style components capable of
  swapping control and guide topologies in a component graph
  clearing DG nodes marked for deletion
  removing the guide DAG entries
More commands might be added later, but for now the above is all the plugin manages
  and all of that work is contained into a single command

The plugin is largely untested and it's a simple port of the script developed
  and used in the late 20s episodes.

This might eventually be used for other didactic purposes, and it also
  includes extensive comments on the cruddy methods required by Maya
  to properly identify a plugin and the commands contained, in case
  it's of some use to anybody.

See repository for license and details at https://github.com/cultofrig/didactic
This software is provided as-is, with no warranties, under the BSD 3-clause license.
"""

from maya.api import _OpenMaya_py2 as om2
from maya import cmds as m_cmds


def maya_useNewAPI():
    """
    This is simple Maya crud.
    The presence of this function is necessary for Maya's registrar to poke
      at the plugin when it's being loaded. If it exists Maya assumes
      this plugin deals with OpenMaya2 objects and not the older OpenMaya.
    It doesn't require an implementation.
    """
    pass


PLUGIN_NAME = 'corps_guidance_commands'
CMD_NAME_SWAPGUIDECONTROL = 'corps_guidance_swapAndOrRemove'

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

    for eachDestinationPlug in plug.destinations():
        destinationNode = eachDestinationPlug.node()
        if not destinationNode.hasFn(om2.MFn.kHyperLayout):
            continue

        # at this point we're dealing with an interesting node
        #  and we should find if it's connected to a container
        mfnDestinationNode = om2.MFnDependencyNode(destinationNode)
        layoutNodeMsgPlug = mfnDestinationNode.findPlug("message", False)

        msgDestinations = layoutNodeMsgPlug.destinations()
        for eachLayoutDestination in msgDestinations:
            if eachLayoutDestination.node().hasFn(om2.MFn.kContainer):
                return eachLayoutDestination.node()


# Just some strings we happen to re-use a lot for keywords.
# All we want is to ensure some consistency
GUIDE_KEY = 'guide'
CONTROL_KEY = 'control'
DEFORM_KEY = 'deform'
TOOLPARAMETERS_SUFFIX = 'toolParameters'

def importantObjectsFromContainer(containerHandle):
    """
    This takes a component name for some filtering and a container handle and isolates
      the key objects related to it that represent our component interesting items.
    :param containerHandle: `MObjectHandle`
    :return: `dict` k,v pairs for interesting objects and their handle, None if unavailable
    """

    mfn_cont = om2.MFnContainerNode(containerHandle.object())
    mobaMembers = mfn_cont.getMembers()

    fullname = mfn_cont.name()
    tokens = fullname.rsplit('_', 1)
    componentName = tokens[0]

    keyObsDict = {
        'componentName': componentName,
        CONTROL_KEY : None,
        GUIDE_KEY : None,
        DEFORM_KEY : None,
        TOOLPARAMETERS_SUFFIX : None,
    }

    toolParametersObjName = '{}_{}'.format(componentName, TOOLPARAMETERS_SUFFIX)
    for eachMob in mobaMembers:
        if not eachMob.hasFn(om2.MFn.kDagNode):
            continue

        mfn_dag = om2.MFnDagNode(eachMob)

        objectName = mfn_dag.name()

        if objectName == CONTROL_KEY:
            keyObsDict[CONTROL_KEY] = om2.MObjectHandle(eachMob)
        elif objectName == GUIDE_KEY:
            keyObsDict[GUIDE_KEY] = om2.MObjectHandle(eachMob)
        elif objectName == DEFORM_KEY:
            keyObsDict[DEFORM_KEY] = om2.MObjectHandle(eachMob)
        elif objectName == toolParametersObjName:
            keyObsDict[TOOLPARAMETERS_SUFFIX] = om2.MObjectHandle(eachMob)

    return keyObsDict


# These are the names of the subPlugs we expect to deal with when
#   dealing with a guided component that has a tools panel to track plugs
TRACKER_PLUG_NAMES = ('origin', 'guided')

def iterSwapPlugs(plug):
    """
    This takes a well formed plug that is an array of compounds with two children
      and yields dictionaries containing those two sub plugs indexed by their expected (shortest) names
    :param plug: `MPlug` Array of Compounds of two plugs
                           with children named as indicated in preceding constant
    :return: `dict` {origin:MPlug, guided:MPlug}
    """
    assert plug.isArray, "input plug is not an array"
    assert plug.isCompound, "plug is not compound"

    elemCount = plug.evaluateNumElements()
    for i in xrange(elemCount):
        plug_swapCpd = plug.elementByPhysicalIndex(i)
        childrenCount = plug_swapCpd.numChildren()
        assert childrenCount == 2, "plug has unexpected number of children"

        trackedPlugsDict = {TRACKER_PLUG_NAMES[0]: None, TRACKER_PLUG_NAMES[1]: None}
        for j in xrange(childrenCount):
            subPlug = plug_swapCpd.child(j)
            plugKey = subPlug.partialName().rsplit('.', 1)[-1]
            trackedPlugsDict[plugKey] = om2.MPlug().copy(subPlug)

        yield trackedPlugsDict


def cmdFriendlyNameFromPlug(plug):
    """
    The function argument names for the call as we need it look ugly, so this
      exists purely for some semantic compression.
    Give a plug it will return the full, command friendly string identifying it
    :param plug: `MPlug | None` a valid Maya Plug, or None to get an empty string
    :return: `str` a string containing the full path, host object included, to the plug
    """
    if plug is None:
        return ''
    return plug.partialName(useFullAttributePath=True,
                            includeNodeName=True,
                            useLongNames=True)


RUN_LOCAL_INSTANCE_MODE = False # If on the class will be able to run without
                                #   being managed by the Maya plugin registrar
                                #   this is only really useful for debug and dev purposes
class SwapGuideControl(om2.MPxCommand):
    """
    General Maya command with flags for CultOfRig style components to operate on
      a general component's guide mode.
     * -swp will swap plugs from the tool parameters pairings as needed to toggle
             a guide's effect on or off
     * -rd  will remove all nodes flagged for deletion by their connection
             to the tool parameters plug
     * -rg  will remove the top DAG object for a component's guide taking the
             hierarchy with it
    """
    __needsUndoing = 0 # Start with None for not set, replace with meaningful int during run
    __containerHandle = None
    __componentDict = dict()
    __toolParsMobha = None

    @classmethod
    def swgc_cmd_creator(cls):
        """
        More Maya crud.
        Maya can't know for sure what classes represent something of interest.
        For a class to work as a Maya extension of its specified type Maya
          chose to use a callback mechanism.
        This means that the class itself is actually registered by the registrar
          inside initialize/uninitialize (see below). The way that registrar works
          is that it expects to receive a function (not some class), and that function
          is responsible to return an instance of the class representing the command.
        This is what makes the name of the class, and of this method for that matter,
          completely irrelevant. It's the act of passing it on to the registrar
          that will make this a plug-in.
        This also offers you an entry point that will only run once for every instance
          of the extension (be it a command run cycle or a node's instantiation in the graph).
        Do bear in mind this is a static method, it's not aware of the class instance itself,
          but it passes a formed class back to the caller (which will be Maya itself).
        :return:
        """
        return cls()


    @staticmethod
    def obSw2xR_stx_creator():
        """
        Not unlike swgc_cmd_creator() above (pun not intended)
        This is a static method to be sent to the registrar, but it's implemented
          as a class method instead to avoid reload issues.
        Unlike the creation function this is optional and only used if you want
          to specify syntax for the command.
        :return: `MSyntax`
        """

        stx = om2.MSyntax()
        stx.setObjectType(om2.MSyntax.kSelectionList, 1, 1)
        stx.useSelectionAsDefault(True)
        # ^^ We do allow for an active selection to pass its first object in
        #       if the command is called with no arguments

        # We don't want to complicate undo work by storing reductions of the selection
        # We limit the command to operate on one object at a time.
        # It's the responsibility of the called to support multiselection as needed.
        stx.addFlag('-sw', '-swapPlugs', om2.MSyntax.kBoolean)
        stx.addFlag('-rd', '-removeDG', om2.MSyntax.kBoolean)
        stx.addFlag('-rg', '-removeDAG', om2.MSyntax.kBoolean)

        return stx


    @staticmethod
    def hasSyntax():
        """
        Maya factory method, indicates a syntax() method should exist, probably
        :return: `bool`
        """
        return True


    @staticmethod
    def isUndoable():
        """
        This is called by Maya on instantiation to know if the command is capable of undoing itself
        :return `bool` we statically return True as we'll implement undo
        """
        return True


    def doIt(self, args):
        """
        Maya Factory method
        :param args: in new-api mode this is probably going to be a tuple
        :return: `None`
        """

        if not RUN_LOCAL_INSTANCE_MODE:
            argDB = om2.MArgDatabase(self.syntax(), args)
            obList = argDB.getObjectList()
            sw = argDB.isFlagSet('-sw')
            rd = argDB.isFlagSet('-rd')
            rg = argDB.isFlagSet('-rg')
        else: # debug only case, set manually as needed
            obList = om2.MGlobal.getActiveSelectionList()
            sw = True
            rd = False
            rg = False

        # We assume there can only be one object in the list we received
        #   based on the constraints we established for the arguments
        mob = obList.getDependNode(0)

        containerNode = containerFromNode(mob)
        self.__containerHandle = om2.MObjectHandle(containerNode)


        if containerNode is None or containerNode.isNull():
            return
        else:
            self.__componentDict = importantObjectsFromContainer(self.__containerHandle)
            self.__toolParsMobha = self.__componentDict[TOOLPARAMETERS_SUFFIX]

            requiresPanel = sw or rg

            if requiresPanel and (self.__toolParsMobha is None or not self.__toolParsMobha.isValid()):
                return

        if sw:
            # This section is responsible for, if invoked, swapping the plugs
            #     that set the state of the component to guided or unguided
            mfn_panelDag = om2.MFnDagNode(self.__toolParsMobha.object())
            plug_toSwap = mfn_panelDag.findPlug('toSwap', False)

            for eachNamedCouple in iterSwapPlugs(plug_toSwap):
                trPlug_origin = eachNamedCouple[TRACKER_PLUG_NAMES[0]] # origin on tracker panel
                trPlug_guided = eachNamedCouple[TRACKER_PLUG_NAMES[1]] # guided on tracker panel

                actPlug_origin = None # source of tracked origin plug, might remain None
                actPlug_originSource = None # source of active origin plug, might remain None
                actPlug_guided = None # source of tracked guided plug, might remain None
                actPlug_guidedSource = None # most upstream plug to swap, might remain None

                if trPlug_origin.isDestination:
                    actPlug_origin = trPlug_origin.source()
                    if actPlug_origin.isDestination:
                        actPlug_originSource = actPlug_origin.source()

                if trPlug_guided.isDestination:
                    actPlug_guided = trPlug_guided.source()
                    if actPlug_guided.isDestination:
                        actPlug_guidedSource = actPlug_guided.source()

                doNothing = (actPlug_origin is None) and (actPlug_guidedSource is None)
                if doNothing:
                    continue
                else: # else is redundant here, it's only for clarity and legibility
                    self.__needsUndoing = 1

                name_trOrigin = cmdFriendlyNameFromPlug(trPlug_origin)
                name_trGuided = cmdFriendlyNameFromPlug(trPlug_guided)

                name_actOrigin = cmdFriendlyNameFromPlug(actPlug_origin)
                name_actOriginSource = cmdFriendlyNameFromPlug(actPlug_originSource)
                name_actGuided = cmdFriendlyNameFromPlug(actPlug_guided)
                name_actGuidedSource = cmdFriendlyNameFromPlug(actPlug_guidedSource)

                connect = actPlug_origin is not None and actPlug_guidedSource is None
                disconnect = actPlug_origin is None and actPlug_guidedSource is not None
                swap = actPlug_origin is not None and actPlug_guidedSource is not None

                if connect:
                    m_cmds.connectAttr(name_actOrigin, name_actGuided)
                    m_cmds.disconnectAttr(name_actOrigin, name_trOrigin)

                elif disconnect:
                    m_cmds.disconnectAttr(name_actGuidedSource, name_actGuided)
                    m_cmds.connectAttr(name_actGuidedSource, name_trOrigin)

                elif swap:
                    m_cmds.connectAttr(name_actGuidedSource, name_trOrigin, force=True)
                    m_cmds.connectAttr(name_actOrigin, name_actGuided, force=True)

                else:
                    # if things get to this point it means that no combination of
                    #   flags ever took place and all cases are False.
                    # This error should literally be impossible since check coverage is complete.
                    # If this occurs something might have mutated the various branching flags
                    #   between checks, which would be extremely unlikely to happen
                    raise RuntimeError("WTF, mate?!")
        # end swap

        if rg:
            # This section, if invoked, is responsible to iterate the plugs
            #     flagging what objects require deletion and issuing
            #     the command to delete each
            mfn_panelDag = om2.MFnDagNode(self.__toolParsMobha.object())
            plug_toDelete = mfn_panelDag.findPlug('toDelete', False)

            elemCount = plug_toDelete.evaluateNumElements()

            foundAtLeastOne = 0
            for i in xrange(elemCount):
                elemPlug = plug_toDelete.elementByPhysicalIndex(i)
                if elemPlug.isDestination:
                    foundAtLeastOne = 2
                    sourceNode = elemPlug.source().node()

                    if sourceNode.hasFn(om2.MFn.kDagNode):
                        om2.MDagPath.getAPathTo(sourceNode)
                        pathToNode = om2.MDagPath.getAPathTo(sourceNode).fullPathName()
                    else:
                        pathToNode = om2.MFnDependencyNode(sourceNode).name()

                    if pathToNode:
                        m_cmds.delete(pathToNode)

            self.__needsUndoing += foundAtLeastOne
        # end delete DG nodes

        if rd:
            # This section, if invoked, is responsible to delete the guide DAG object
            #     for the component, which should take with it the entire hierarchy
            guideMobha = self.__componentDict[GUIDE_KEY]
            if guideMobha is None or not guideMobha.isValid() or guideMobha.object().isNull():
                self.__needsUndoing = self.__needsUndoing or 0
                return

            guideMob = guideMobha.object()
            assert guideMob.hasFn(om2.MFn.kDagNode), "guide object stored in dictionary doesn't seem to be a DAG node"

            pathToGuide = om2.MDagPath.getAPathTo(guideMobha.object()).fullPathName()
            m_cmds.delete(pathToGuide)
        # end delete DAG node


    @staticmethod
    def undoIt():
        """
        Maya expects this method to exist and to be able to call it if the command
          is flagged as undoable. Since all we use is a bunch of commands
          undoing is relatively trivial, and we can just call Maya's own undo
          and let it go over the chunk of commands that was ran during doIt()
        Normally this wouldn't be static as it might need to access something from
          inside the instance of the command class that was run, but when
          all these methods do is call a one-liner Maya command there really
          is no reason for them to be more than a static wrapper of the factory undo call.
        :return: `None`
        """
        m_cmds.undo()


    @staticmethod
    def redoIt():
        """
        See docstring for undoIt() above. This is equivalent except for redoing
          instead of undoing.
        :return: `None`
        """
        m_cmds.redo()



def initializePlugin(mob):
    """
    This function is necessary for Maya to be able to operate on this file as a plug-in.
    When the registrar inspects the files it's been passed it will allocate
      space somewhere to register a plug-in, then call this function inside the module
      and pass it that location (as an MObject, which is most likely a pointer with lipstick on)
      for the function to be able to register various commands or nodes or whatever else MPx
      supports that you want to make Maya aware of and responsible for.
    :param mob: `MObject` Some black boxed entry point for Maya to manage this plug-in
    :return: `None`
    """
    fnPlugin = om2.MFnPlugin(mob)
    fnPlugin.setName(PLUGIN_NAME)

    fnPlugin.registerCommand(CMD_NAME_SWAPGUIDECONTROL,
                             SwapGuideControl.swgc_cmd_creator,
                             SwapGuideControl.obSw2xR_stx_creator)


def uninitializePlugin(mob):
    """
    See initializePlugin docstring, this is symmetrical and opposite to that.
    It will be responsible to de-register everything that initialize registered with the Maya client session
    :param mob: `MObject` Some black boxed entry point for Maya to manage this plug-in
    :return: `None`
    """
    fnPlugin = om2.MFnPlugin(mob)
    fnPlugin.deregisterCommand(CMD_NAME_SWAPGUIDECONTROL)

