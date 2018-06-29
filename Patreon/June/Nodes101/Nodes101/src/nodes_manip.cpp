# include "../headers/nodes.h"

MTypeId TrigManip::id(0x81047);
MString TrigManip::name("trigManipulator");


TrigManip::TrigManip() {
    centre_point = MPoint(0.0, 0.0, 0.0, 1.0);
    end_point = MPoint(0.0, 0.0, 0.0, 1.0);

    manip_plane_normal = MVector(0.0, 0.0, -1.0);
}


TrigManip::~TrigManip() {}

void TrigManip::postConstructor() {


}

void TrigManip::draw(M3dView& view, const MDagPath& path,
                     M3dView::DisplayStyle disp_style, M3dView::DisplayStatus disp_status) {
    // In VP2 this still does work but only for selection.
    // In VP1 this can called FFP and draw as well

    static MGLFunctionTable* gGLFT = 0;
}

void TrigManip::preDrawUI(const M3dView & view) {
    //in VP2 this sets up all custom data that drawing the UI might require
}

void TrigManip::drawUI(const M3dView & view) {
    // the actual drawing of the UI in VP2, VP1 will still do so in draw.
    // VP2 still uses draw() for the selection process
    //   probably on account of that being CPU side (I'd guess)

}

MStatus TrigManip::doPress(M3dView & view) {
    return MS::kUnknownParameter; // default return for Maya to handle calls
}

MStatus TrigManip::doDrag(M3dView & view) {
    return MS::kUnknownParameter; // default return for Maya to handle calls
}

MStatus TrigManip::doRelease(M3dView & view) {
    return MS::kUnknownParameter; // default return for Maya to handle calls
}

MStatus TrigManip::connectToDependNode(const MObject & dependNode) {
    return MStatus();
}

