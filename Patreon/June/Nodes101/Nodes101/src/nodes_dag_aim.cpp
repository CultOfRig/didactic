#include "../headers/nodes.h"


//               -= MATRIX =-
MTypeId AimMatrix::id = MATRIX_AIM_ID;

AimMatrix::AimMatrix(){};

void* AimMatrix::creator() {
    return new AimMatrix();
}

MMatrix AimMatrix::asMatrix() const {
    return matrixFromInternals();
}

MMatrix AimMatrix::asMatrix(double percent) const {
    return matrixFromInternals();
}


MMatrix AimMatrix::matrixFromInternals() const {

    MFloatVector at = aim - position;
    at.normalize();

    MFloatVector binormal = at ^ (up - position);
    binormal.normalize();

    MFloatVector normal = binormal ^ at;

    double mtx[4][4];
    mtx[0][0] = at.x;       mtx[0][1] = at.y;       mtx[0][2] = at.z;       mtx[0][3] = 0.0;
    mtx[1][0] = normal.x;   mtx[1][1] = normal.y;   mtx[1][2] = normal.z;   mtx[1][3] = 0.0;
    mtx[2][0] = binormal.x; mtx[2][1] = binormal.y; mtx[2][2] = binormal.z; mtx[2][3] = 0.0;
    mtx[3][0] = position.x; mtx[3][1] = position.y; mtx[3][2] = position.z; mtx[3][3] = 1.0;

    double mtx_conversion_aa[4][4];
    inverse_parent_space.get(mtx_conversion_aa);
    MMatrix local_inverse(mtx_conversion_aa);

    return MMatrix(mtx) * local_inverse;
}



//               -=  NODE  =-
MTypeId AimTransform::id = NODE_AIM_ID;
MString AimTransform::name = NODE_AIM_NAME;

MObject AimTransform::inverse_parent_space_smob;
MObject AimTransform::driver_position_smob;
MObject AimTransform::driver_at_smob;
MObject AimTransform::driver_up_smob;


AimTransform::AimTransform() : ParentClass() {}

AimTransform::AimTransform(MPxTransformationMatrix* p_mtx) : ParentClass(p_mtx) {}

AimTransform::~AimTransform() {}


void * AimTransform::creator() {
    return new AimTransform();
}

MStatus AimTransform::initialize() {
    MStatus status;

    MFnMatrixAttribute fn_matrix;

    inverse_parent_space_smob = fn_matrix.create("inverse_parent_world_space", "inverse_parent_world_space",
                                                 MFnMatrixAttribute::kFloat, &status);
    fn_matrix.setWritable(true); fn_matrix.setStorable(true); fn_matrix.setConnectable(true);
    fn_matrix.setAffectsWorldSpace(true);

    driver_position_smob = fn_matrix.create("driver_world_position", "driver_world_position",
                                            MFnMatrixAttribute::kFloat, &status);
    fn_matrix.setWritable(true); fn_matrix.setStorable(true); fn_matrix.setConnectable(true);
    fn_matrix.setAffectsWorldSpace(true);

    driver_at_smob = fn_matrix.create("driver_world_at", "driver_world_at",
                                      MFnMatrixAttribute::kFloat, &status);
    fn_matrix.setWritable(true); fn_matrix.setStorable(true); fn_matrix.setConnectable(true);
    fn_matrix.setAffectsWorldSpace(true);

    driver_up_smob = fn_matrix.create("driver_world_up", "driver_world_up",
                                      MFnMatrixAttribute::kFloat, &status);
    fn_matrix.setWritable(true); fn_matrix.setStorable(true); fn_matrix.setConnectable(true);
    fn_matrix.setAffectsWorldSpace(true);

    addAttribute(inverse_parent_space_smob);
    addAttribute(driver_position_smob);
    addAttribute(driver_at_smob);
    addAttribute(driver_up_smob);

    attributeAffects(inverse_parent_space_smob, matrix);
    attributeAffects(driver_position_smob, matrix);
    attributeAffects(driver_at_smob, matrix);
    attributeAffects(driver_up_smob, matrix);

    mustCallValidateAndSet(inverse_parent_space_smob);
    mustCallValidateAndSet(driver_position_smob);
    mustCallValidateAndSet(driver_at_smob);
    mustCallValidateAndSet(driver_up_smob);

    return status;
}


static MFloatVector posRowFromMatrix(MFloatMatrix m) {
    float position_row[3] = {0.f, 0.f, 0.f};
    constexpr auto size_of_row = sizeof(float)* 3;

    memcpy(position_row, m[3], size_of_row);
    return MFloatVector(position_row);
}


MStatus AimTransform::validateAndSetValue(const MPlug& plug,
                                          const MDataHandle& hdl){
    auto p_output_mtx = static_cast<AimMatrix*>(transformationMatrixPtr());

    if(plug == driver_position_smob){
        auto driver_position_mtx = hdl.asFloatMatrix();
        
        p_output_mtx->position = posRowFromMatrix(driver_position_mtx);
    }

    else if(plug == driver_at_smob || plug == driver_up_smob){
        MStatus status;
        MDataBlock datablock = forceCache();
        MDataHandle driver_at_hdl = datablock.inputValue(driver_at_smob, &status);
        MDataHandle driver_up_hdl = datablock.inputValue(driver_up_smob, &status);

        auto driver_at_mtx = driver_at_hdl.asFloatMatrix();
        auto driver_up_mtx = driver_up_hdl.asFloatMatrix();

        p_output_mtx->aim = posRowFromMatrix(driver_at_mtx);
        p_output_mtx->up = posRowFromMatrix(driver_up_mtx);
    }

    else if(plug == inverse_parent_space_smob){
        p_output_mtx->inverse_parent_space = hdl.asFloatMatrix();
    }

    return ParentClass::validateAndSetValue(plug, hdl);
}


MPxTransformationMatrix* AimTransform::createTransformationMatrix() {
    return new AimMatrix();
}


MStatus AimTransform::compute(const MPlug& plug, MDataBlock& datablock) {
    return MPxTransform::compute(plug, datablock);
}


