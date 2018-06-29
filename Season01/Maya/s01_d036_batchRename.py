from maya.api import OpenMaya as om2
from maya import cmds as m_cmds

sel = om2.MGlobal.getActiveSelectionList()
selCount = sel.length()

trimLength = len('toChange')

hasActed = False
dg_mod = om2.MDGModifier()
for i in xrange(selCount):
    currMob = sel.getDependNode(i)
    fn = om2.MFnDependencyNode(currMob)
    
    currName = fn.name()
    
    newName = currName.replace('_R_', '_L_')[trimLength:]
    if m_cmds.objExists(newName):
        continue
    else:
        hasActed = True
        dg_mod.renameNode(currMob, newName)

if hasActed:    
    dg_mod.doIt()
    m_cmds.flushUndo()
