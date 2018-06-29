#include <maya/MFnPlugin.h>

#include "../headers/nodes.h"



MStatus initializePlugin(MObject pluginMob) {
    MStatus status;
    MFnPlugin fn(pluginMob);

    status = fn.setName("Nodes101");

    /* DG NODES */
    status = fn.registerNode(SinNode::name, SinNode::id,
                             &SinNode::creator, &SinNode::initialize,
                             MPxNode::kDependNode, nullptr);

    status = fn.registerNode(CosNode::name, CosNode::id,
                             &CosNode::creator, &CosNode::initialize,
                             MPxNode::kDependNode, nullptr);

    /* DAG NODES */
    status = fn.registerTransform(StaticHrc::name, StaticHrc::id,
                                  &StaticHrc::creator, &StaticHrc::initialize,
                                  &StaticMatrix::creator,
                                  StaticMatrix::id, nullptr);

    status = fn.registerTransform(AimTransform::name, AimTransform::id,
                                  &AimTransform::creator, &AimTransform::initialize,
                                  &AimMatrix::creator,
                                  AimMatrix::id, nullptr);

    return MS::kSuccess;
}



MStatus uninitializePlugin(MObject pluginMob) {
    MFnPlugin fn(pluginMob);

    fn.deregisterNode(SinNode::id);
    fn.deregisterNode(CosNode::id);

    fn.deregisterNode(StaticHrc::id);
    fn.deregisterNode(AimTransform::id);

    return MS::kSuccess;
}
