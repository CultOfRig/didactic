from maya.api import _OpenMaya_py2 as om2

def is_control_rig(mob):
    fn = om2.MFnDagNode(mob)
    is_named_correctly = fn.name() == "rig"

    is_two_from_world = False
    if (is_named_correctly):
        parent_mob = fn.parent(0)
        parent_fn = om2.MFnDagNode(parent_mob)

        if parent_fn.name() != 'world':
            granny_mob = parent_fn.parent(0)
            granny_fn = om2.MFnDagNode(granny_mob)

            is_two_from_world = granny_fn.name() == 'world'

    return is_named_correctly and is_two_from_world


def is_component(mob):
    fn = om2.MFnDagNode(mob)

    is_under_rig = is_control_rig(fn.parent(0))
    if is_under_rig:
        return fn.name().endswith('_cmpnt')
    else:
        return False


def iter_components(rig_mob):
    if is_control_rig(rig_mob):
        fn = om2.MFnDagNode(rig_mob)
        child_count = fn.childCount()

        for i in range(child_count):
            child_mob = fn.child(i)
            child_name = om2.MFnDagNode(child_mob).name()
            if child_name.endswith('_cmpnt'):
                yield child_mob

                
def container_from_component(component_mob):
    assert is_component(component_mob)

    comp_fn = om2.MFnDagNode(component_mob)
    comp_dag_name = comp_fn.name()

    container_name = "{}_container".format(comp_dag_name[:-6])

    sel = om2.MSelectionList()
    sel.add(container_name)

    container_mob = sel.getDependNode(0)

    return container_mob


def iter_component_members(component_mob):
    container_fn = om2.MFnContainerNode(container_from_component(component_mob))

    members = container_fn.getMembers()
    for each_member in members:
        yield each_member


def iter_input(component_mob):
    if is_component(component_mob):
        fn = om2.MFnDagNode(component_mob)
        child_count = fn.childCount()

        for i in range(child_count):
            child_mob = fn.child(i)
            child_name = om2.MFnDagNode(child_mob).name()
            if child_name.endswith('_input'):
                yield child_mob


def iter_output(component_mob):
    if is_component(component_mob):
        fn = om2.MFnDagNode(component_mob)
        child_count = fn.childCount()

        for i in range(child_count):
            child_mob = fn.child(i)
            child_name = om2.MFnDagNode(child_mob).name()
            if child_name.endswith('_output'):
                yield child_mob

                itr_dag = om2.MItDag()
                itr_dag.reset(child_mob)
                itr_dag.next()

                while (not itr_dag.isDone()):
                    curr_node = itr_dag.currentItem()

                    yield curr_node
                    itr_dag.next()
            