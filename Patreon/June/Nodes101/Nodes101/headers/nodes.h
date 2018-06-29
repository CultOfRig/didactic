#ifndef DG_NODES_GUARD
#define DG_NODES_GUARD

#include <maya/MGlobal.h>

#include <maya/MPxNode.h>
#include <maya/MPxTransform.h>
#include <maya/MPxTransformationMatrix.h>
#include <maya/MPxManipContainer.h>

#include <maya/MFnUnitAttribute.h>
#include <maya/MFnNumericAttribute.h>
#include <maya/MFnMatrixAttribute.h>

#include <maya/MFloatMatrix.h>
#include <maya/MAngle.h>

#include <cmath>

/*      DG       */
static const int NODE_TRIG_SIN_ID = 0x0012a23f;
static const char* NODE_TRIG_SIN_NAME = "trig_sin";

static const int NODE_TRIG_COS_ID = 0x0012a23e;
static const char* NODE_TRIG_COS_NAME = "trig_cos";


/*      DAG      */
static const int MATRIX_STATICHRC_ID = 0x0012a23d;
static const int MATRIX_AIM_ID = 0x0012a23c;

static const int NODE_STATICHRC_ID = 0x0012a23b;
static const char* NODE_STATICHRC_NAME = "static_hrc";

static const int NODE_AIM_ID = 0x0012a23a;
static const char* NODE_AIM_NAME = "aim_transform";

#endif // !DG_NODES_GUARD



/*  +---------------------+
    |       DG NODES      |
    +---------------------+   */
/*           sin              */
class SinNode : public MPxNode {
public:
    SinNode();
    virtual ~SinNode();

    virtual MStatus compute(const MPlug& plug, MDataBlock& datablock);

    static void* creator();
    static MStatus initialize();

    static MTypeId id;
    static MString name;

    static MObject operand_smob;
    static MObject result_smob;
};


/*           cos              */
class CosNode : public MPxNode {
public:
    CosNode();
    virtual ~CosNode();

    virtual MStatus compute(const MPlug& plug, MDataBlock& datablock);

    static void* creator();
    static MStatus initialize();

    static MTypeId id;
    static MString name;

    static MObject operand_smob;
    static MObject result_smob;
};



/*  +---------------------+
    |       DAG NODES     |
    +---------------------+   */

/*  STATIC                    */
/*      static matrix         */
class StaticMatrix : public MPxTransformationMatrix {
public:
    StaticMatrix();
    
    static void* creator();

    virtual MMatrix asMatrix() const;
    virtual MMatrix asMatrix(double percent) const;

    static MTypeId id;

protected:
    typedef MPxTransformationMatrix ParentClass;
};


/*      static node           */
class StaticHrc : public MPxTransform {
public:
    static MTypeId id;
    static MString name;

    StaticHrc();
    StaticHrc(MPxTransformationMatrix*);
    virtual ~StaticHrc();

    static void* creator();
    static MStatus initialize();
    void postConstructor();

    MPxTransformationMatrix* createTransformationMatrix();

    virtual MStatus compute(const MPlug& plug, MDataBlock& datablock);

protected:
    typedef MPxTransform ParentClass;
};


/*  AIM                       */
/*        aim matrix          */
class AimMatrix : public MPxTransformationMatrix {
public:
    AimMatrix();

    static void* creator();

    virtual MMatrix asMatrix() const;
    virtual MMatrix asMatrix(double percent) const;

    MFloatMatrix inverse_parent_space;
    MFloatVector position;
    MFloatVector aim;
    MFloatVector up;

    static MTypeId id;

protected:
    typedef MPxTransformationMatrix ParentClass;

private:
    MMatrix matrixFromInternals() const;
};

/*        aim node            */
class AimTransform : public MPxTransform {
// members
public:
    // factory
    static MTypeId id;
    static MString name;

    // additional
    static MObject inverse_parent_space_smob;
    static MObject driver_position_smob;
    static MObject driver_at_smob;
    static MObject driver_up_smob;

// methods
public:
    // factory
    AimTransform();
    AimTransform(MPxTransformationMatrix*);
    virtual ~AimTransform();

    static void* creator();
    static MStatus initialize();



    MStatus validateAndSetValue(const MPlug&,
                                const MDataHandle&) override;

    MPxTransformationMatrix* createTransformationMatrix();

    virtual MStatus compute(const MPlug& plug, MDataBlock& datablock);

protected:
    typedef MPxTransform ParentClass;
};



class TrigManip : public MPxManipulatorNode {
public:
    static MTypeId id;
    static MString name;

    TrigManip();
    ~TrigManip();
    virtual void postConstructor();

    virtual void draw(M3dView& view, const MDagPath& path,
                      M3dView::DisplayStyle disp_style, M3dView::DisplayStatus disp_status);

    void preDrawUI(const M3dView& view);
    void drawUI(const M3dView& view);

    virtual MStatus doPress(M3dView& view);
    virtual MStatus doDrag(M3dView& view);
    virtual MStatus doRelease(M3dView& view);

    virtual MStatus connectToDependNode(const MObject &dependNode);

private:
    MPoint centre_point;
    MPoint end_point;

    MVector manip_plane_normal;

};