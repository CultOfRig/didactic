#include "../headers/nodes.h"


//               -= MATRIX =-
MTypeId StaticMatrix::id = MATRIX_STATICHRC_ID;

StaticMatrix::StaticMatrix(){};

void* StaticMatrix::creator() {
    return new StaticMatrix();
}

MMatrix StaticMatrix::asMatrix() const {
    return MMatrix::identity;
}

MMatrix StaticMatrix::asMatrix(double percent) const {
    return MMatrix::identity;
}



//               -=  NODE  =-
MTypeId StaticHrc::id = NODE_STATICHRC_ID;
MString StaticHrc::name = NODE_STATICHRC_NAME;

StaticHrc::StaticHrc() : ParentClass() {}

StaticHrc::StaticHrc(MPxTransformationMatrix* p_mtx) : ParentClass(p_mtx) {}

StaticHrc::~StaticHrc() {}


void * StaticHrc::creator() {
    return new StaticHrc();
}

MStatus StaticHrc::initialize() {
    return MStatus::kSuccess;
}


void StaticHrc::postConstructor(){
    ParentClass::postConstructor();
}

MPxTransformationMatrix* StaticHrc::createTransformationMatrix() {
    return new StaticMatrix();
}


MStatus StaticHrc::compute(const MPlug& plug, MDataBlock& datablock) {
    return MStatus::kSuccess;
}
