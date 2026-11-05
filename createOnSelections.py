import maya.cmds as cmds


def create_ui():
    if cmds.window("myWindow", exists=True):
        cmds.deleteUI("myWindow")

    window = cmds.window("myWindow", title="Title", wh=(420, 250), s=False)

    cmds.columnLayout(adjustableColumn=True, rowSpacing=10)
    cmds.text(l=" ", al='right')

    grid = cmds.gridLayout(nc=2, cellWidthHeight=(150, 28))

    cmds.text(l="Obj Name:    ", al='right')
    cmds.textField("objName", width=180, text="name")

    cmds.text(l="Creation Method:    ", al='right')
    cmds.optionMenu("methodMenu")
    cmds.menuItem(l="Bounding Box")
    cmds.menuItem(l="Each Position")
    cmds.menuItem(l="Edge Length")
    cmds.menuItem(l="Curve Cv")
    cmds.menuItem(l="Curve Length")
    cmds.menuItem(l="Curve Parmeter")

    cmds.text(l="Creation Type:    ", al='right')
    cmds.optionMenu("typeMenu")
    cmds.menuItem(l="Joint")
    cmds.menuItem(l="Locator")
    cmds.menuItem(l="Null")

    cmds.text(l="Division:    ", al='right')
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
    objName = cmds.textField("objName", q=True, text=True)
    method = cmds.optionMenu("methodMenu", q=True, v=True)
    obj_type = cmds.optionMenu("typeMenu", q=True, v=True)
    division = cmds.intField("divisionField", q=True, v=True)
    reverse = cmds.checkBox("reverseCB", q=True, v=True)
    chain = cmds.checkBox("chainCB", q=True, v=True)

    create(method, obj_type, division, baseName=objName, reverse=reverse, chain=chain)


def create(creationMethod, objType, division, baseName, reverse, chain):
    creationMethod = creationMethod.lower().replace(" ", "")
    objType = objType.lower().replace(" ", "")
    # print(creationMethod)
    # print(objType)
    counter = [1]

    def getPositionsByMethod(obj, method, division):
        positions = []

        # accroding to Bounding Box
        if method == "boundingbox":
            shapes = cmds.listRelatives(obj, s=True, f=True)

            meshShapes = [s for s in shapes if cmds.objectType(s) == "mesh"]

            if meshShapes:
                bb = cmds.exactWorldBoundingBox(obj)
                centerX = (bb[0] + bb[3]) / 2.0
                centerY = (bb[1] + bb[4]) / 2.0
                centerZ = (bb[2] + bb[5]) / 2.0
                positions.append([centerX, centerY, centerZ])

        # accroding to Curve CV
        elif method == "curvecv":
            selectedObj = cmds.ls(sl=True, type="nurbsCurve", dag=True)

            if not selectedObj:
                trans = cmds.ls(sl=True, type="transform")
                for obj in trans:
                    shapes = cmds.listRelatives(obj, s=True, type="nurbsCurve")
                    selectedObj.extend(shapes)

            for crv in selectedObj:
                # Get all CVs of the curve
                cvs = cmds.ls(f"{crv}.cv[*]", fl=True)
                for cv in cvs:
                    pos = cmds.pointPosition(cv, w=True)
                    positions.append(pos)

            return positions

            # accroding to Curve Length
        elif method == "curvelength":
            base_crv = obj
            deg = cmds.getAttr(base_crv + '.degree')
            tmp_crv = base_crv + '_tmpRebuilt'
            cmds.rebuildCurve(base_crv, n=tmp_crv, ch=False, replaceOriginal=False,
                              rt=0, end=True, kr=0, kcp=False,
                              kep=True, kt=False, s=division - 1, d=deg)
            shape = cmds.listRelatives(tmp_crv, s=True, f=True)[0]
            min_u = cmds.getAttr(f"{shape}.minValue")
            max_u = cmds.getAttr(f"{shape}.maxValue")

            # for near Point on curve
            tmp_npc = base_crv + '_npc'
            npc = cmds.createNode("nearestPointOnCurve", n=tmp_npc)
            baseCurveShape = cmds.listRelatives(base_crv, s=True)[0]
            cmds.connectAttr(baseCurveShape + ".worldSpace[0]", npc + ".inputCurve", f=True)

            for i in range(division):
                stepRatio = float(i) / (division - 1)
                param = min_u + stepRatio * (max_u - min_u)
                pos = cmds.pointOnCurve(tmp_crv, pr=param, p=True, top=True)
                cmds.setAttr(npc + ".inPosition", pos[0], pos[1], pos[2], type="double3")
                closestParam = cmds.getAttr(npc + ".parameter")
                closetpos = cmds.pointOnCurve(base_crv, pr=closestParam, p=True)
                positions.append(closetpos)
            cmds.delete(tmp_crv)
            cmds.delete(npc)

        # accroding to Edge Length
        elif method == "edgelength":
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
                base_crv = cmds.polyToCurve(form=2, degree=1, ch=False)[0]
                deg = 1
                tmp_crv = base_crv + '_tmpRebuilt'
                cmds.rebuildCurve(base_crv, n=tmp_crv, ch=False, replaceOriginal=False,
                                  rt=0, end=True, kr=0, kcp=False,
                                  kep=True, kt=False, s=division - 1, d=deg)
                shape = cmds.listRelatives(tmp_crv, s=True, f=True)[0]
                min_u = cmds.getAttr(f"{shape}.minValue")
                max_u = cmds.getAttr(f"{shape}.maxValue")

                # for near Point on curve
                tmp_npc = base_crv + '_npc'
                npc = cmds.createNode("nearestPointOnCurve", n=tmp_npc)
                baseCurveShape = cmds.listRelatives(base_crv, s=True)[0]
                cmds.connectAttr(baseCurveShape + ".worldSpace[0]", npc + ".inputCurve", f=True)

                for i in range(division):
                    stepRatio = float(i) / (division - 1)
                    param = min_u + stepRatio * (max_u - min_u)
                    pos = cmds.pointOnCurve(tmp_crv, pr=param, p=True, top=True)

                    cmds.setAttr(npc + ".inPosition", pos[0], pos[1], pos[2], type="double3")
                    closestParam = cmds.getAttr(npc + ".parameter")
                    newPos = cmds.pointOnCurve(base_crv, pr=closestParam, p=True)

                    positions.append(newPos)
                cmds.delete(npc)
                cmds.delete(tmp_crv)
                cmds.delete(base_crv)

        # accroding to Curve Parmeter
        elif method == "curveparmeter":
            base_crv = obj
            deg = cmds.getAttr(base_crv + '.degree')
            tmp_crv = base_crv
            shape = cmds.listRelatives(tmp_crv, s=True, f=True)[0]
            min_u = cmds.getAttr(f"{shape}.minValue")
            max_u = cmds.getAttr(f"{shape}.maxValue")
            step = (max_u - min_u) / (division - 1)

            for i in range(division):
                param = min_u + (step * i)
                pos = cmds.pointOnCurve(tmp_crv, pr=param, p=True)
                positions.append(pos)
        return positions

    def getPositionsFromComponents():
        sel = cmds.ls(selection=True, flatten=True)
        posList = []
        for comp in sel:
            pos = None
            if '.vtx[' in comp:
                pos = cmds.pointPosition(comp, world=True)
            elif '.e[' in comp or '.f[' in comp:
                verts = cmds.polyListComponentConversion(comp, toVertex=True)
                verts = cmds.ls(verts, flatten=True)
                if verts:
                    sum_pos = [0.0, 0.0, 0.0]
                    for v in verts:
                        p = cmds.pointPosition(v, world=True)
                        sum_pos[0] += p[0]
                        sum_pos[1] += p[1]
                        sum_pos[2] += p[2]
                    count = len(verts)
                    pos = [sum_pos[0] / count, sum_pos[1] / count, sum_pos[2] / count]
            else:
                print("need to select vtx, edge or face")

            if pos:
                posList.append(pos)

        return posList

    def createObjAtPos(pos, name, par=None):
        # print(par)
        if objType == "joint":
            suffix = "jnt"

            x_axis = (1, 0, 0)
            y_up = (0, 1, 0), (0, 1, 0)
            primary = x_axis
            up_vec, world_up_vec = y_up

            obj = cmds.createNode("joint")
            cmds.xform(obj, ws=True, t=pos)
            if chain and par:
                temp_loc = cmds.spaceLocator(n=name + "loc")[0]
                cmds.xform(temp_loc, ws=True, t=pos)
                cmds.delete(cmds.aimConstraint(temp_loc, par, aim=primary, u=up_vec, wut="scene", wu=world_up_vec))
                cmds.makeIdentity(par, apply=True, rotate=True)
                cmds.delete(temp_loc)



        elif objType == "locator":
            suffix = "loc"
            shape = cmds.spaceLocator()[0]
            obj = shape
            cmds.xform(obj, ws=True, t=pos)
        else:
            suffix = "off"
            obj = cmds.createNode("transform")
            cmds.xform(obj, ws=True, t=pos)

        obj = cmds.rename(obj, f"{name}_{suffix}")
        return obj

    if creationMethod == "eachposition":
        allPositions = getPositionsFromComponents()
        if reverse:
            allPositions = list(reversed(allPositions))
        last_created = None
        for pos in allPositions:
            created = createObjAtPos(pos, f"{baseName}_{counter[0]}", last_created)
            counter[0] += 1
            if chain and last_created:
                cmds.parent(created, last_created)
            last_created = created

    elif creationMethod == "boundingbox":
        allPositions = []
        selObjs = cmds.ls(sl=True, flatten=True)
        for obj in selObjs:
            posList = getPositionsByMethod(obj, creationMethod, division=None)
            if posList:
                allPositions.extend(posList)
        if reverse:
            allPositions = list(reversed(allPositions))

        last_created = None
        for i in range(len(allPositions) - 1):
            startPos = allPositions[i]
            endPos = allPositions[i + 1]

            created = createObjAtPos(startPos, f"{baseName}_{counter[0]}", last_created)
            counter[0] += 1
            if chain and last_created:
                cmds.parent(created, last_created)
            last_created = created

            for d in range(1, division + 1):
                stepRatio = float(d) / (division + 1)
                interpPos = [
                    startPos[0] + (endPos[0] - startPos[0]) * stepRatio,
                    startPos[1] + (endPos[1] - startPos[1]) * stepRatio,
                    startPos[2] + (endPos[2] - startPos[2]) * stepRatio,
                ]
                created = createObjAtPos(interpPos, f"{baseName}_{counter[0]}", last_created)
                counter[0] += 1
                if chain and last_created:
                    cmds.parent(created, last_created)
                last_created = created

        created = createObjAtPos(allPositions[-1], f"{baseName}_{counter[0]}", last_created)
        if chain and last_created:
            cmds.parent(created, last_created)

    elif creationMethod == "curveparmeter" or "curvecv" or "edgelength" or "curvelength":
        if creationMethod in ["edgelength", "curveparmeter", "curvelength"] and division <= 2:
            cmds.warning(creationMethod + " method works only when division is greater than 2,")
            return
        selObjs = cmds.ls(sl=True, fl=True)
        for curveIndex, obj in enumerate(selObjs, start=1):
            posList = getPositionsByMethod(obj, creationMethod, division)
            if not posList:
                continue

            if reverse:
                posList = list(reversed(posList))

            last_created = None
            for cvIndex, pos in enumerate(posList, start=1):
                name = f"{baseName}_{curveIndex}_{cvIndex}"
                created = createObjAtPos(pos, name, last_created)

                if chain and last_created:
                    cmds.parent(created, last_created)
                last_created = created

            if objType == "joint" and chain and last_created:
                cmds.joint(last_created, e=True, oj="none", ch=True, zso=True)


create_ui()


