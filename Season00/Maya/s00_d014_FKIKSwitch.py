
fkik_attrName = 'FKIK_switch'

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


def removeCallbacksFromNode(node_mob):
    """
    :param node_mob: [MObject] the node to remove all node callbacks from
    :return: [int] number of callbacks removed
    """
    cbs = om2.MMessage.nodeCallbacks(node_mob)
    cbCount = len(cbs)
    for eachCB in cbs:
        om2.MMessage.removeCallback(eachCB)
    return cbCount


def removeCallbacksFromSel():
    """
    Will remove all callbacks from each node in the current selection
    :return: [(int, int)] total number of objects that had callbacks removed,
                            and total count of all callbacks removed across them
    """
    cbCount = 0
    mobCount = 0
    for eachMob in iterSelection():
        mobCount += 1
        cbCount += removeCallbacksFromNode(eachMob)
    return mobCount, cbCount


def cb(msg, plug1, plug2, payload):
    if msg != 2056: #check most common case first and return unless it's
        return      # an attribute edit type of callback

    if not plug1.partialName(includeNodeName=False, useAlias=False) == fkik_attrName:
        # We ensure if the attribute being changed is uninteresting we do nothing
        return

    isFK = plug1.asBool() == False # Switched To FK
    isIK = not isFK # Switched to IK

    settingsAttrs = { # all interesting attribute names in keys, respective plugs in values
                     'fkRotation': None,
                     'ikRotation': None,
                     'fk_ctrl_rotx': None,
                     'ik_ctrl_translate': None,
                     'ikPedalOffset': None,
                     }

    mfn_dep = om2.MFnDependencyNode(plug1.node())
    # We populate the dictionary of interesting attributes with their plugs
    for eachPName in settingsAttrs.iterkeys():
        plug = mfn_dep.findPlug(eachPName, False)
        settingsAttrs[eachPName] = plug

    for p in settingsAttrs.itervalues():
        # We will exit early and do nothing if a plug couldn't be initialised, the object
        #  is malformed, or we installed the callback on an object that is only
        #  conformant by accident and can't operate as we expect it to.
        if p is None:
            return

    angle = None # empty init
    if isFK:
        # Simplest case, if we switched to FK we copy the roation from IK
        #  to the FK control's X rotation value
        angle = -settingsAttrs.get("ikRotation").source().asDouble()
        fkSourcePlug = settingsAttrs.get("fk_ctrl_rotx").source()
        fkSourcePlug.setDouble(angle)
    elif isIK:
        # If instead we switched to IK we need to
        #  derive the translation of the IK control that produces the result
        #  of an equivalent rotation to the one coming from the FK control
        angle = settingsAttrs.get("fkRotation").source().asDouble()
        projectedLen = settingsAttrs.get("ikPedalOffset").source().asDouble()

        y = ( math.cos(angle) * projectedLen ) - projectedLen
        z = math.sin(angle) * projectedLen

        ikSourcePlug = settingsAttrs.get("ik_ctrl_translate").source()
        for i in xrange(ikSourcePlug.numChildren()):
            realName = ikSourcePlug.child(i).partialName(includeNodeName = False, useAlias = False)
            if realName == 'ty':
                ikSourcePlug.child(i).setDouble(y)
            elif realName == 'tz':
                ikSourcePlug.child(i).setDouble(z)


removeCallbacksFromSel()
for eachMob in iterSelection():
    om2.MNodeMessage.addAttributeChangedCallback(eachMob, cb)