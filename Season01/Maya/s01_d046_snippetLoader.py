"""
A somewhat horrifying way to load, reload etc. our snippets for the day.
Also starts the debug server.
Made to be loaded in the Maya shell to type inline tests while
   we get small functions rolling
"""

try:
    from Maya import s01_d046_rigItemIteration as snips
    reload(snips)
    print("reloading")
except:
    import ptvsd
    ptvsd.enable_attach(address=('0.0.0.0', 3000), redirect_output=True)

    k_path = "" # Your directory goes here

    from sys import path

    found = False
    for x in path:
        if x == k_path:
            found = True
            break
    
    if not found:
        path.append(k_path)
        print("Appended new path to sys called {}".format(k_path))

    from Maya import s01_d046_snippets as snips
    reload(snips)

    print("first time loading {}".format(snips))
    

from maya.api import OpenMaya as om2

sel = om2.MGlobal.getActiveSelectionList()

for i in range(sel.length()):
    mob = sel.getDependNode(i)
    if snips.is_control_rig(sel.getDependNode(i)):
        for comp in snips.iter_components(mob):
            for m in snips.iter_component_members(comp):
                print om2.MFnDependencyNode(m).name()
    
