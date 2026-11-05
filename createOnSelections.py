
import maya.cmds as cmds


def create_ui():
    if cmds.window("myWindow", exists=True):
        cmds.deleteUI("myWindow")

    window = cmds.window("myWindow", title="Title", wh=(370, 220), s=False)

    cmds.columnLayout(adjustableColumn=True, rowSpacing=10)
    cmds.text(l=" ", al='right')

    grid = cmds.gridLayout(nc=2, cellWidthHeight=(140, 25))

    cmds.text(l="Creation Method: ", al='right')
    option1 = cmds.optionMenu("methodMenu")
    cmds.menuItem(l="Edge Length")

    cmds.text(l="Creation Type: ", al='right')
    option2 = cmds.optionMenu("typeMenu")
    cmds.menuItem(l="Joint")
    cmds.menuItem(l="Locator")
    cmds.menuItem(l="Null")

    cmds.text(l="Division:", al='right')
    cmds.intField("divisionField", value=5)

    cmds.text(l="")
    reverseVal = cmds.checkBox("reverseCB", l="Reverse", v=False)

    cmds.text(l="")
    chainVal = cmds.checkBox("chainCB", l="Chain", v=False)

    cmds.text(l="")
    cmds.button(label="Create", command=run_creator)

    cmds.setParent('..')

    cmds.showWindow(window)


def run_creator(*args):
    method = cmds.optionMenu("methodMenu", q=True, v=True)
    obj_type = cmds.optionMenu("typeMenu", q=True, v=True)
    division = cmds.intField("divisionField", q=True, v=True)
    reverse = cmds.checkBox("reverseCB", q=True, v=True)
    chain = cmds.checkBox("chainCB", q=True, v=True)

    create(method, obj_type, division, baseName="name",
           reverse=reverse, chain=chain)


def create(creationMethod, objType, division, baseName, reverse, chain):

    creationMethod = creationMethod.lower().replace(" ", "")
    objType = objType.lower().replace(" ", "")

    counter = [1]

    def getPositionsByMethod(obj, method, division):
        positions = []

        if method == "edgelength":
            sel = cmds.ls(sl=True, fl=True)

            if not sel:
                print("edge selection only.")

            else:
                all_edges = True

                for s in sel:
                    if ".e[" not in s:
                        all_edges = False
                        break

                if not all_edges:
                    return

                cmds.select(sel, replace=True)

                base_crv = cmds.polyToCurve(
                    form=2, degree=1, ch=False
                )[0]

                deg = 1
                tmp_crv = base_crv + '_tmpRebuilt'

                cmds.rebuildCurve(
                    base_crv,
                    n=tmp_crv,
                    ch=False,
                    replaceOriginal=False,
                    rt=0,
                    end=True,
                    kr=0,
                    kcp=False,
                    kep=True,
                    kt=False,
                    s=division - 1,
                    d=deg
                )

                shape = cmds.listRelatives(
                    tmp_crv, s=True, f=True
                )[0]

                min_u = cmds.getAttr(shape + ".minValue")
                max_u = cmds.getAttr(shape + ".maxValue")

                for i in range(division):
                    fraction = float(i) / (division - 1) if division > 1 else 0.0

                    param = min_u + fraction * (max_u - min_u)

                    pos = cmds.pointOnCurve(
                        tmp_crv, pr=param, p=True, top=True
                    )

                    positions.append(pos)

                cmds.delete(tmp_crv)
                cmds.delete(base_crv)

        return positions

    def getPositionsFromComponents():
        # vtx, edge, face

        sel = cmds.ls(selection=True, flatten=True)
        posList = []

        for comp in sel:
            pos = None

            if '.vtx[' in comp:
                pos = cmds.pointPosition(comp, world=True)

            elif '.e[' in comp or '.f[' in comp:
                verts = cmds.polyListComponentConversion(
                    comp, toVertex=True
                )

                verts = cmds.ls(verts, flatten=True)

                if verts:
                    sum_pos = [0.0, 0.0, 0.0]

                    for v in verts:
                        p = cmds.pointPosition(v, world=True)

                        sum_pos[0] += p[0]
                        sum_pos[1] += p[1]
                        sum_pos[2] += p[2]

                    count = len(verts)

                    pos = [
                        sum_pos[0] / count,
                        sum_pos[1] / count,
                        sum_pos[2] / count
                    ]

            else:
                print("Need to select vtx, edge or face")

            if pos:
                posList.append(pos)

        return posList

    def createObjAtPos(pos, name):

        if objType == "joint":
            suffix = "jnt"
            obj = cmds.createNode("joint")

        elif objType == "locator":
            suffix = "loc"
            shape = cmds.spaceLocator()[0]
            obj = shape

        else:
            suffix = "off"
            obj = cmds.createNode("transform")

        obj = cmds.rename(obj, name + '_' + suffix)

        cmds.xform(obj, ws=True, t=pos)

        return obj

    if creationMethod == "eachposition":

        allPositions = getPositionsFromComponents()

        if not allPositions:
            return

        if reverse:
            allPositions = list(reversed(allPositions))

        last_created = None

        for pos in allPositions:

            created = createObjAtPos(
                pos,
                baseName + '_' + str(counter[0])
            )

            counter[0] += 1

            if chain and last_created:
                cmds.parent(created, last_created)

            last_created = created

    elif creationMethod == "edgelength":

        selectedObjects = cmds.ls(sl=True, flatten=True)

        for curveIndex, obj in enumerate(selectedObjects, start=1):

            posList = getPositionsByMethod(
                obj, creationMethod, division
            )

            if not posList:
                continue

            if reverse:
                posList = list(reversed(posList))

            last_created = None

            for cvIndex, pos in enumerate(posList, start=1):

                name = (
                    baseName + '_' +
                    str(curveIndex) + '_' +
                    str(cvIndex)
                )

                created = createObjAtPos(name=name, pos=pos)

                if chain and last_created:
                    cmds.parent(created, last_created)

                last_created = created


create_ui()
