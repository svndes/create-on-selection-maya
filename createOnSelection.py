"""
createOnSelection.py
====================
Maya utility that creates joints, locators, or null transforms at positions
derived from a selection.  Supported placement methods:
 
    Bounding Box   – one object per selected mesh, at its world-space centre
    Each Position  – one object per selected vertex / edge / face
    Edge Length    – N objects distributed evenly along selected edges
    Curve CV       – one object per CV on a selected NURBS curve
    Curve Length   – N objects distributed evenly along a NURBS curve
 
Usage
-----
Run the script in Maya's Script Editor (Python tab).  A small UI window will
appear.  Select geometry in the viewport, configure options, then press Create.
 
Author : Sandesh Chakradhar
Version: 1.0
"""

import maya.cmds as cmds
import string


def onCreateButtonClick(*args):
    method  = cmds.optionMenu("methodMenu", q=True, v=True)
    objType = cmds.optionMenu("typeMenu",   q=True, v=True)
    div     = cmds.intFieldGrp('divFld',    q=True, v1=True)

    name = cmds.textField("nameFld", q=True, text=True)
    node = cmds.textField("nodeFld", q=True, text=True)
    expr = cmds.textField("exprFld", q=True, text=True)

    reverse = cmds.checkBoxGrp("rvrsCB", q=True, v1=True)
    chain   = cmds.checkBoxGrp("chnCB",  q=True, v1=True)

    if cmds.ls(sl=True):
        doCreate(method, objType, div,
                 name=name, node=node, expr=expr,
                 reverse=reverse, chain=chain)
    else:
        cmds.warning("Select Object")


def onTypeChange(*args):
    objType = cmds.optionMenu("typeMenu", q=True, v=True)
    mapping = {
        "Joint":   "jnt",
        "Locator": "loc",
        "Null":    "off"
    }
    cmds.textField("nodeFld", e=True, text=mapping.get(objType, ""))


def onMethodChange(*args):
    method = cmds.optionMenu("methodMenu", q=True, v=True)
    descriptions = {
        "Bounding Box":   "Places objects at each mesh's bounding box center.",
        "Each Position":  "Places objects at each selected vtx / edge / face.",
        "Edge Length":    "Distributes objects evenly along selected edges.",
        "Curve Cv":       "Places objects at each CV point on a curve.",
        "Curve Length":   "Distributes objects evenly by curve length.",
    }
    cmds.text("descTxt", e=True, l=descriptions.get(method, ""))

    # enable Division / Reverse / Chain only when method needs them
    needsDivision = method not in ("Bounding Box", "Each Position")
    cmds.intFieldGrp("divFld",  e=True, en=needsDivision)
    cmds.checkBoxGrp("rvrsCB",  e=True, en=needsDivision)
    cmds.checkBoxGrp("chnCB",   e=True, en=needsDivision)


def buildName(name, node, expr, counter, alpha_counter):
    resolved = expr
    if '#' in expr:
        resolved = resolved.replace('#', str(counter))
    if '@' in expr:
        letter = string.ascii_uppercase[alpha_counter % 26]
        resolved = resolved.replace('@', letter)

    parts = [p for p in [name, node, resolved] if p]
    return '_'.join(parts)


def doCreate(creationMethod, objType, division,
             name, node, expr,
             reverse, chain):
    creationMethod = creationMethod.lower().replace(" ", "")
    objType        = objType.lower().replace(" ", "")

    counter = [1, 0]

    def getPosByMethod(obj, method, division):
        positions = []

        if method == "boundingbox":
            sel = cmds.ls(sl=True, flatten=True)
            validMeshes = []
        
            for obj in sel:
                shapes = cmds.listRelatives(obj, s=True, f=True) or []
                meshShapes = [s for s in shapes if cmds.objectType(s) == "mesh"]
                if meshShapes:
                    validMeshes.append(obj)
                else:
                    cmds.warning(f"'{obj}' is not a polygon mesh — skipped.")
        
            if not validMeshes:
                cmds.warning("No valid polygon meshes in selection.")
                return positions
        
            for mesh in validMeshes:
                bb      = cmds.exactWorldBoundingBox(mesh)
                centerX = (bb[0] + bb[3]) / 2.0
                centerY = (bb[1] + bb[4]) / 2.0
                centerZ = (bb[2] + bb[5]) / 2.0
                positions.append([centerX, centerY, centerZ])

        elif method == "curvecv":
            selectedObj = cmds.ls(sl=True, type="nurbsCurve", dag=True)
            if not selectedObj:
                trans = cmds.ls(sl=True, type="transform")
                for o in trans:
                    shapes = cmds.listRelatives(o, s=True, type="nurbsCurve") or []
                    selectedObj.extend(shapes)
        
            if not selectedObj:
                cmds.warning("Please select a NURBS curve.")
                return positions
        
            if len(selectedObj) > 1:
                cmds.warning("Only one curve allowed for Curve CV method. Using first curve only.")
                selectedObj = [selectedObj[0]]
        
            for crv in selectedObj:
                cvs = cmds.ls(f"{crv}.cv[*]", fl=True)
                for cv in cvs:
                    pos = cmds.pointPosition(cv, w=True)
                    positions.append(pos)
            return positions
        
        elif method == "curvelength":
            allSel   = cmds.ls(sl=True, flatten=True)
            curveObj = []
        
            for o in allSel:
                shapes = cmds.listRelatives(o, s=True, type="nurbsCurve") or []
                if shapes:
                    curveObj.append(o)
                else:
                    objType = cmds.objectType(cmds.listRelatives(o, s=True, f=True)[0]) if cmds.listRelatives(o, s=True) else "unknown"
                    if objType != "nurbsCurve":
                        cmds.warning(f"'{o}' is not a NURBS curve — skipped.")
        
            if not curveObj:
                cmds.warning("Please select a NURBS curve.")
                return positions
        
            if len(curveObj) > 1:
                cmds.warning("Only one curve allowed for Curve Length method. Using first curve only.")
                curveObj = [curveObj[0]]
        
            base_crv = curveObj[0]
            deg      = cmds.getAttr(base_crv + '.degree')
            tmp_crv  = base_crv + '_tmpRebuilt'
            cmds.rebuildCurve(base_crv, n=tmp_crv, ch=False, replaceOriginal=False,
                              rt=0, end=True, kr=0, kcp=False,
                              kep=True, kt=False, s=division - 1, d=deg)
            shape = cmds.listRelatives(tmp_crv, s=True, f=True)[0]
            minU  = cmds.getAttr(f"{shape}.minValue")
            maxU  = cmds.getAttr(f"{shape}.maxValue")
        
            tmp_npc        = base_crv + '_npc'
            npc            = cmds.createNode("nearestPointOnCurve", n=tmp_npc)
            baseCurveShape = cmds.listRelatives(base_crv, s=True)[0]
            cmds.connectAttr(baseCurveShape + ".worldSpace[0]", npc + ".inputCurve", f=True)
        
            for i in range(division):
                stepRatio    = float(i) / (division - 1)
                param        = minU + stepRatio * (maxU - minU)
                pos          = cmds.pointOnCurve(tmp_crv, pr=param, p=True, top=True)
                cmds.setAttr(npc + ".inPosition", pos[0], pos[1], pos[2], type="double3")
                closestParam = cmds.getAttr(npc + ".parameter")
                closetpos    = cmds.pointOnCurve(base_crv, pr=closestParam, p=True)
                positions.append(closetpos)
        
            cmds.delete(tmp_crv)
            cmds.delete(npc)
    
    

        elif method == "edgelength":
            sel = cmds.ls(sl=True, fl=True)
            if not sel:
                print("edge selection only.")
            else:
                all_edges = all(".e[" in s for s in sel)
                if not all_edges:
                    return
                cmds.select(sel, replace=True)
                base_crv = cmds.polyToCurve(form=2, degree=1, ch=False)[0]
                tmp_crv  = base_crv + '_tmpRebuilt'
                cmds.rebuildCurve(base_crv, n=tmp_crv, ch=False, replaceOriginal=False,
                                  rt=0, end=True, kr=0, kcp=False,
                                  kep=True, kt=False, s=division - 1, d=1)
                shape = cmds.listRelatives(tmp_crv, s=True, f=True)[0]
                minU  = cmds.getAttr(f"{shape}.minValue")
                maxU  = cmds.getAttr(f"{shape}.maxValue")

                tmp_npc        = base_crv + '_npc'
                npc            = cmds.createNode("nearestPointOnCurve", n=tmp_npc)
                baseCurveShape = cmds.listRelatives(base_crv, s=True)[0]
                cmds.connectAttr(baseCurveShape + ".worldSpace[0]", npc + ".inputCurve", f=True)

                for i in range(division):
                    stepRatio = float(i) / (division - 1)
                    param     = minU + stepRatio * (maxU - minU)
                    pos       = cmds.pointOnCurve(tmp_crv, pr=param, p=True, top=True)
                    cmds.setAttr(npc + ".inPosition", pos[0], pos[1], pos[2], type="double3")
                    closestParam = cmds.getAttr(npc + ".parameter")
                    newPos       = cmds.pointOnCurve(base_crv, pr=closestParam, p=True)
                    positions.append(newPos)
                cmds.delete(npc)
                cmds.delete(tmp_crv)
                cmds.delete(base_crv)


        return positions

    def getPosFromSel():
        sel     = cmds.ls(selection=True, flatten=True)
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
                    pos = [c / len(verts) for c in sum_pos]
            else:
                cmds.warning("need to select vtx, edge or face")
            if pos:
                posList.append(pos)
        return posList

    def createObjAtPos(pos, objName, par=None):
        if objType == "joint":
            x_axis             = (1, 0, 0)
            up_vec, world_up_vec = (0, 1, 0), (0, 1, 0)
            obj = cmds.createNode("joint")
            cmds.xform(obj, ws=True, t=pos)
            if chain and par:
                temp_loc = cmds.spaceLocator(n=objName + "loc")[0]
                cmds.xform(temp_loc, ws=True, t=pos)
                cmds.delete(cmds.aimConstraint(temp_loc, par,
                                               aim=x_axis, u=up_vec,
                                               wut="scene", wu=world_up_vec))
                cmds.makeIdentity(par, apply=True, rotate=True)
                cmds.delete(temp_loc)
        elif objType == "locator":
            obj = cmds.spaceLocator()[0]
            cmds.xform(obj, ws=True, t=pos)
        else:
            obj = cmds.createNode("transform")
            cmds.xform(obj, ws=True, t=pos)

        obj = cmds.rename(obj, objName)
        return obj

    def nextName():
        n = buildName(name, node, expr, counter[0], counter[1])
        counter[0] += 1
        counter[1] += 1
        return n

    # ── creation methods ─────────────────────────────────────────────────────

    if creationMethod == "eachposition":
        allPositions = getPosFromSel()
        if reverse:
            allPositions = list(reversed(allPositions))
        last_created = None
        for pos in allPositions:
            created = createObjAtPos(pos, nextName(), last_created)
            if chain and last_created:
                cmds.parent(created, last_created)
            last_created = created
            
            
    elif creationMethod == "boundingbox":
        sel = cmds.ls(sl=True, flatten=True)
        last_created = None
    
        for obj in sel:
            shapes     = cmds.listRelatives(obj, s=True, f=True) or []
            meshShapes = [s for s in shapes if cmds.objectType(s) == "mesh"]
    
            if not meshShapes:
                cmds.warning(f"'{obj}' is not a polygon mesh — skipped.")
                continue
    
            bb      = cmds.exactWorldBoundingBox(obj)
            centerX = (bb[0] + bb[3]) / 2.0
            centerY = (bb[1] + bb[4]) / 2.0
            centerZ = (bb[2] + bb[5]) / 2.0
            pos     = [centerX, centerY, centerZ]
    
            created = createObjAtPos(pos, nextName(), last_created)
            if chain and last_created:
                cmds.parent(created, last_created)
            last_created = created     
                

               

    elif creationMethod in ( "curvecv", "edgelength", "curvelength"):
        if creationMethod in ("edgelength", "curvelength") and division <= 2:
            cmds.warning(creationMethod + " method works only when division is greater than 2.")
            return

        for obj in cmds.ls(sl=True, fl=True):
            counter[0] = 1
            counter[1] = 0
            posList = getPosByMethod(obj, creationMethod, division)
            if not posList:
                continue
            if reverse:
                posList = list(reversed(posList))
            last_created = None
            for pos in posList:
                created = createObjAtPos(pos, nextName(), last_created)
                if chain and last_created:
                    cmds.parent(created, last_created)
                last_created = created
            if objType == "joint" and chain and last_created:
                cmds.joint(last_created, e=True, oj="none", ch=True, zso=True)
                                
def openCreateOnSelUI():
    win = "createOnSel"
    if cmds.window(win, exists=True):
        cmds.deleteUI(win)

    cmds.window(win, title='Create On Selection - UI', widthHeight=(300, 300))
    form   = cmds.formLayout()
    tabs   = cmds.tabLayout(innerMarginWidth=5, bs='full', tv=False)
    t1 = cmds.columnLayout(adj=True, rowSpacing=5, columnOffset=['both', 5])

    cmds.separator(h=8,style="none")
    cmds.text("descTxt", l="Places objects at each mesh's bounding box center.",
              h=22, en=True, align='center', font="obliqueLabelFont", bgc=[0.55, 0.55, 0.55])
    cmds.separator(h=10)

    # ── Name / Node / Expression on one line 
    cmds.rowLayout(nc=4, columnWidth4=[50, 70, 60, 40], columnAlign4=['right', 'left', 'left', 'left'])
    cmds.text(l="Name :", w=58)
    cmds.textField("nameFld", w=70, text='obj')
    cmds.textField("nodeFld", w=60, text='jnt')
    cmds.textField("exprFld", w=40, text='#', ann="Use # for numbers (1,2,3…) or @ for letters (A,B,C…)")
    cmds.setParent('..')

    cmds.separator(h=5)

    # ── Method 
    cmds.rowLayout(nc=2, columnWidth2=[70, 105], columnAlign2=['right', 'left'])
    cmds.text(l="Method :", w=68)
    cmds.optionMenu("methodMenu", w=105, changeCommand=onMethodChange)
    cmds.menuItem(l="Bounding Box")
    cmds.menuItem(l="Each Position")
    cmds.menuItem(l="Edge Length")
    cmds.menuItem(l="Curve Cv")
    cmds.menuItem(l="Curve Length")
    cmds.setParent('..')

    # ── Type 
    cmds.rowLayout(nc=2, columnWidth2=[70, 80], columnAlign2=['right', 'left'])
    cmds.text(l="Type :", al='right', w=68)
    cmds.optionMenu("typeMenu", w=75, changeCommand=onTypeChange)
    cmds.menuItem(l="Joint")
    cmds.menuItem(l="Locator")
    cmds.menuItem(l="Null")
    cmds.setParent('..')

    cmds.separator(h=10)
    cmds.intFieldGrp('divFld', numberOfFields=1, label='Division : ', cw2=[70, 40], v1=5, en=False)

    cmds.checkBoxGrp("rvrsCB", l="Reverse : ", ncb=1, v1=False, cw2=[70, 50], en=False)
    cmds.checkBoxGrp("chnCB",  l="Chain : ",   ncb=1, v1=False, cw2=[70, 50], en=False)

    cmds.separator(h=10)
    cmds.button(l="create", h=60, bgc=[0.1, 0.2, 0.3], command=onCreateButtonClick)
    cmds.separator(h=2,style="none")

    cmds.setParent('..')  

    cmds.tabLayout(tabs, edit=True, tabLabel=[(t1, "")])
    cmds.formLayout(form, edit=True,
                    attachForm=[(tabs, 'top', 5), (tabs, 'left', 5),
                                (tabs, 'bottom', 5), (tabs, 'right', 5)])
    cmds.showWindow()


openCreateOnSelUI()
