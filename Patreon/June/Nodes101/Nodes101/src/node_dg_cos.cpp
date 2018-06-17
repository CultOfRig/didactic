#include "../headers/nodes.h"


MTypeId CosNode::id = NODE_TRIG_COS_ID;
MString CosNode::name = NODE_TRIG_COS_NAME;
MObject CosNode::operand_smob;
MObject CosNode::result_smob;


CosNode::CosNode(){}

CosNode::~CosNode(){}

void* CosNode::creator() {
    return new CosNode();
}


MStatus CosNode::initialize() {
    MStatus status;

    MFnUnitAttribute fn_unit;

    operand_smob = fn_unit.create("operand", "operand", MFnUnitAttribute::kAngle, 0.0, &status);
    fn_unit.setStorable(true);
    fn_unit.setWritable(true);
    fn_unit.setKeyable(true);

    MFnNumericAttribute fn_numeric;

    result_smob = fn_numeric.create("result", "result", MFnNumericData::kDouble, 0.0, &status);
    fn_numeric.setStorable(false);
    fn_numeric.setWritable(false);
    fn_numeric.setKeyable(false);

    addAttribute(operand_smob);
    addAttribute(result_smob);

    attributeAffects(operand_smob, result_smob);

    return status;
}


MStatus CosNode::compute(const MPlug& plug, MDataBlock& datablock) {
    if( plug == result_smob ) {
        MStatus status;

        MDataHandle operand_hdl = datablock.inputValue(operand_smob, &status);
        MAngle operand = operand_hdl.asAngle();
        double result = std::cos(operand.asRadians());

        MDataHandle result_hdl = datablock.outputValue(result_smob, &status);
        result_hdl.setDouble(result);

        result_hdl.setClean();
        return status;
    }
    else {
        return MStatus::kUnknownParameter;
    }
}
