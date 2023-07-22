## Call of Duty Map Importer for Maya by MrChuse
## https://twitter.com/MrChuse
## Version 2.0.4


import maya.cmds as cmds
import maya.mel as mel
import os as os



def GetMapFile():
    global mapFilePath
    filename = cmds.fileDialog2(fileMode=1, caption="Import Map File")
    mapFilePath = filename[0]

def GetModelFolder():
    global modelFolderPath
    filename = cmds.fileDialog2(fileMode=2, caption="Select Model Folder")
    modelFolderPath = filename[0]
    # print(modelFolderPath)

def ImportMapOBJ():
    global OBJFile
    try:
        cmds.file(OBJFile, i=True, mergeNamespaceWithRoot=True)
    except:
        print("File not valid")

def QuarttoCoord(quart):
    angle = (quart * 0.000015259022 * 2) - 1
    # return (value / (2 * Math.PI)) * 360;
    return angle

def inch2meter(value):
    result = value * 2.54
    return result

def SaveAsAlembic():
    global mapFilePath
    if bool(cmds.checkBox("abc_export", q=True, v=True)) == True:
        cmds.loadPlugin("AbcExport.mll")
        AbcFile = mapFilePath[:-3] + "abc"
        AbcCommand = "-frameRange " + "1 1" + " -uvWrite -worldSpace " + " -file " + AbcFile
        cmds.AbcExport( j = AbcCommand )
  
# GetMapFile()  
# GetModelFolder()

def MakeModelList():
    mapFilePath = cmds.textField("mapFile", q=True, tx=True)
    mapFile = open(mapFilePath, "r")
    modelList = []
    for line in mapFile:
        if line.startswith('"model"'):
            ModelName = line.replace('"','').split()[1]
            if ModelName not in modelList:
                modelList.append(ModelName)
    mapFile.close()
    xmodelFile = open(mapFilePath[:-4] + "_xmodelList.txt", "w")
    for model in modelList:
        xmodelFile.write(model + ", ")
    xmodelFile.close()
    print("Model list created")
    
def TextureList4Mats():
    OBJFile = cmds.textField("OBJFile", q=True, tx=True)
    OBJMaterials = open(OBJFile[:-4] + "_OBJMaterials.txt", "w")
    cmds.refresh(suspend=True)
    # cmds.file(OBJFile, i=True)
    Mats = cmds.ls(type="phong")
    for mat in Mats:
        OBJMaterials.write(mat + ", ")
    OBJMaterials.close()

def getBoundingBox():
    x, y, z = [],[],[]
    obj = cmds.ls(selection=True)[0]
    vtx = cmds.ls(obj+'.vtx[*]', fl=True)
    print(vtx)

    for vert in vtx:
        Coords = cmds.xform(vert, q=True, translation=True, worldSpace=True)
        x.append(round(Coords[0], 2))
        y.append(round(Coords[1], 2))
        z.append(round(Coords[2], 2))

    BBox = {
        'x': (min(x), max(x)),
        'y': (min(y), max(y)),
        'z': (min(z), max(z))
    }

    return BBox

def BBoxCheck(Model, BoundingBox:dict) -> bool:
    if BBox == False:
        return True
    
    if inch2meter(float(Model[0])) >= BoundingBox['x'][0] and inch2meter(float(Model[0])) <= BoundingBox['x'][1]:
        if inch2meter(float(Model[1])) >= BoundingBox['y'][0] and inch2meter(float(Model[1])) <= BoundingBox['y'][1]:
            if inch2meter(float(Model[2])) >= BoundingBox['z'][0] and inch2meter(float(Model[2])) <= BoundingBox['z'][1]:
                return True
            else:
                return False
        else:
            return False
    else:
        return False
    

def Main():
    global OBJFile
    global ModelRotations
    OBJFile = ""
    entities = 0
    Models = []
    ModelName = ""
    ModelOrigin = ""
    ModelRotations = []
    ModelScale = ""
    objectCounter = 0
    mapFilePath = cmds.textField("mapFile", q=True, tx=True)
    modelFolderPath = cmds.textField("xmodels_folder", q=True, tx=True)
    OBJFile = cmds.textField("OBJFile", q=True, tx=True)

    if bool(cmds.checkBox("disable_viewport", q=True, v=True)) == True:
        cmds.refresh(suspend=True)
    # mel.eval("SaveScene();")
    if bool(cmds.checkBox("use_bbox", q=True, v=True)) ==True:
        BBox = True
        BoundingBox = getBoundingBox()
    ImportMapOBJ()
    cmds.mayaUSDExport(file=mapFilePath[:-3] + "usda")
    mapFile = open(mapFilePath, "r")
    

    # Setup Progress Window
    cmds.progressWindow(title="Map Importer",status="Importing...",progress=0,ii=False)
    for line in mapFile:
        if line.startswith('// entity'):
            entities = int(line[10:])
    mapFile.seek(0)
    
    def GameCheck():
        global ModelRotations
        Game = cmds.optionMenu('game', q=True, v=True)
        if Game == "Other":
            ModelMapRot = ModelRotations
            # print(ModelRotations)
            try:
                ModelRotations = ModelMapRot[2], ModelMapRot[0], ModelMapRot[1]
            except:
                print("List out of range")

    # Read and load models
    for line in mapFile:
        if line.startswith('// entity'):
            cmds.progressWindow(edit=True,progress=int(line[10:])/entities*100)
        if line.startswith('"model"'):
            ModelName = line.replace('"','').split()[1]
            # print("Model Name: ", ModelName)
        elif line.startswith('"origin"'):
            ModelOrigin = line[9:].replace('"', '').split()
            # print("Model Origin: ", ModelOrigin)
        elif line.startswith('"angles"'):
            ModelRotations = line[9:].replace('"', '').split()
            # print("Model Rotations", ModelRotations)
        elif line.startswith('"modelscale"'):
            ModelScale = line[13:].replace('"', '')
            # print("Model Scale: ", ModelScale, "\n")
        
        # Start Importing Models
        if line.startswith('"modelscale"'):
            GameCheck()
            #If the model is a duplicate
            if BBoxCheck(ModelOrigin, BoundingBox) == True:
                if ModelName in Models:
                    DupModel = ""
                    NumberBool = False
                    ScaleBool = False
                    try:
                        if str(cmds.getAttr(ModelName + "|Joints.scale")[0]) != 0:
                            OldScale = str(cmds.getAttr(ModelName + ".scale")[0])
                            ScaleBool = True
                            cmds.setAttr(ModelName + '.scale', 1, 1, 1)
                    except:
                        None
                    try:
                        if str(cmds.getAttr(ModelName + "1|Joints.scale")[0]) != 0:
                            OldScale = str(cmds.getAttr(ModelName + ".scale")[0])
                            ScaleBool = True
                            cmds.setAttr(ModelName + '.scale', 1, 1, 1)
                    except:
                        None
                    try:
                        if int(ModelName[-1:]) in range(10):
                            NumberBool = True
                    except:
                        NumberBool = False
                    
                    # If model doesn't end in a number
                    try:
                        ModelDupeGroup = cmds.duplicate(ModelName + '_Group', rr=True, un=True)[0]
                        cmds.ungroup('group')
                        def getShadingGroup(MeshTransform):
                            objMesh = cmds.listRelatives(MeshTransform, shapes=True, fullPath=True)[0]
                            objSE = cmds.listConnections(objMesh, type="shadingEngine")[0]
                            return objSE

                        def getMaterial(MeshTransform):
                            objMesh = cmds.listRelatives(MeshTransform, shapes=True, fullPath=True)[0]
                            objSE = cmds.listConnections(objMesh, type="shadingEngine")[0]
                            objMat = cmds.listConnections(objSE + '.surfaceShader')[0]
                            return objMat         
                    except:
                        None
                    try:
                        if ScaleBool == True:
                            cmds.setAttr(ModelName + '|Joints.scale', OldScale, OldScale, OldScale)
                    except:
                        None
                    try:
                        if ScaleBool == True:
                            cmds.setAttr(ModelName + '1|Joints.scale', OldScale, OldScale, OldScale)
                    except:
                        None
                    try:
                        cmds.setAttr(str(ModelDupeGroup) + '|Joints' + '.translate', inch2meter(float(ModelOrigin[0])), inch2meter(float(ModelOrigin[1])), inch2meter(float(ModelOrigin[2])))
                        cmds.setAttr(str(ModelDupeGroup) + '|Joints' +  '.rotate', (float(ModelRotations[0])), (float(ModelRotations[1])), (float(ModelRotations[2])))
                        cmds.setAttr(str(ModelDupeGroup) + '|Joints' +  '.scale', (float(ModelScale)), (float(ModelScale)), (float(ModelScale)))
                        # print("Duplicate Model moved to: ", ModelOrigin[0], ModelOrigin[1], ModelOrigin[2])
                    except:
                        None
                # Import Model
                else:
                    # print("Importing Model")
                    objectCounter = objectCounter + 1
                    
                    if cmds.ls(geometry=True) != [] and objectCounter >= 100:
                        cmds.mayaUSDExport(file=mapFilePath[:-3] + "usda", append=True)
                        cmds.file(newFile=True,force=True)
                        objectCounter = 0

                    melImportModel = '''file -import -type "SEModel Models"  -ignoreVersion -ra true -mergeNamespacesOnClash false -namespace ""-pr  -importTimeRange "combine" "''' + str(modelFolderPath).replace("\\", "/") + "/" + str(ModelName) + '/' + str(ModelName) + '_LOD0.semodel";'
                
                    try:
                        mel.eval(melImportModel)          
                    except:
                        #print("Model not found: " + str(ModelName))
                        None

                    #Translate, Rotate and ScaleObject
                    try:
                        cmds.setAttr('Joints.translate', inch2meter(float(ModelOrigin[0])), inch2meter(float(ModelOrigin[1])), inch2meter(float(ModelOrigin[2])), type="double3")
                        cmds.setAttr('Joints.rotate', (float(ModelRotations[0])), (float(ModelRotations[1])), (float(ModelRotations[2])))
                        cmds.setAttr('Joints.scale', (float(ModelScale)), (float(ModelScale)), (float(ModelScale)))
                    except:
                        None
                    try:
                        cmds.setAttr('|Joints.translate', inch2meter(float(ModelOrigin[0])), inch2meter(float(ModelOrigin[1])), inch2meter(float(ModelOrigin[2])))
                        cmds.setAttr('|Joints.rotate', (float(ModelRotations[0])), (float(ModelRotations[1])), (float(ModelRotations[2])))
                        cmds.setAttr('|Joints.scale', (float(ModelScale)), (float(ModelScale)), (float(ModelScale)))
                    except:
                        None
                    try:
                        cmds.setAttr('Joints1.translate', inch2meter(float(ModelOrigin[0])), inch2meter(float(ModelOrigin[1])), inch2meter(float(ModelOrigin[2])))
                        cmds.setAttr('Joints1.rotate', (float(ModelRotations[0])), (float(ModelRotations[1])), (float(ModelRotations[2])))
                        cmds.setAttr('Joints1.scale', (float(ModelScale)), (float(ModelScale)), (float(ModelScale)))
                    except:
                        None

                    # Group Objects
                    try:
                        cmds.group('Joints', ModelName + "_LOD0",  n=ModelName + '_Group')
                    except:
                        None
                    try:
                        cmds.group('|Joints', "|" + str(ModelName) + "_LOD0",  n=ModelName + '_Group')
                    except:
                        None
                    Models.append(ModelName)
    cmds.mayaUSDExport(file=mapFilePath[:-3] + "usda", append=True)
    cmds.file(newFile=True,force=True)
    cmds.progressWindow(ep=True)
    mapFile.close()
    SaveAsAlembic()
    # mel.eval("SaveScene();")
# mel.eval("exit")

WINDOW_TITLE = "Call of Duty Material Tool"
WINDOW_WIDTH = 400

ROW_SPACING = 2
PADDING = 5

def addColumnLayout():
    cmds.columnLayout(adjustableColumn=True, columnAttach=('both', PADDING))
    
def addFrameColumnLayout(label, collapsable):
    cmds.frameLayout(collapsable=collapsable, label=label)
    addColumnLayout()

def addInnerRowLayout(numberOfColumns):
    cmds.rowLayout(
        numberOfColumns=numberOfColumns,
        bgc=[0,0,0]
    )

def addDoubleRowLayout():
    cmds.rowLayout(
        numberOfColumns=2, 
        adjustableColumn2=2, 
        columnWidth2=[120, 20],
        columnAlign2=['right', 'left'], 
        columnAttach2=['right', 'left']
    )

def parentToLayout():
    cmds.setParent('..')

def addSpacer():
    cmds.columnLayout(adjustableColumn=True)
    cmds.separator(height=PADDING, style="none")
    parentToLayout()
    
def addHeader(windowTitle):
    addColumnLayout()
    cmds.text(label='<span style=\"color:#ccc;text-decoration:none;font-size:20px;font-family:courier new;font-weight:bold;\">' + windowTitle + '</span>', height=50)
    parentToLayout()
    
def addText(label):
    return cmds.text(label='<span style=\"color:#ccc;text-decoration:none;font-size:px;font-family:courier new;font-weight:bold;\">' + label + '</span>')
    
def addButton(label, command):
    cmds.separator(height=ROW_SPACING, style="none")
    controlButton = cmds.button(label=label, command=(command))
    cmds.separator(height=ROW_SPACING, style="none")
    return controlButton
    
def addButtonNoCommand(label):
    cmds.separator(height=ROW_SPACING, style="none")
    controlButton = cmds.button(label=label)
    cmds.separator(height=ROW_SPACING, style="none")
    return controlButton
        
def addIntField():
    return cmds.intFieldGrp()
        
def addIntSlider():
    return cmds.intFieldGrp()
        
# Int Slider
def addIntSliderGroup(min, max, value):
    return cmds.intSliderGrp(field=True, minValue=min, maxValue=max, fieldMinValue=min, fieldMaxValue=max, value=value)
        
# Float Slider
def addFloatSliderGroup(min, max, value):
    return cmds.floatSliderGrp(field=True, minValue=min, maxValue=max, fieldMinValue=min, fieldMaxValue=max, value=value)
    
# Checkbox
def addCheckboxOld(label):
    return cmds.checkBox(label=label)

def addCheckbox(identifier, label,cc = None, value=False):
    cmds.checkBox(identifier,label=str(label),cc=str(cc),v=bool(value))

# Radio Button
def startRadioButtonCollection():
    return cmds.radioCollection()
    
def addRadioButton(label):
    return cmds.radioButton(label=label)
    
# Object Selection List
def addToObjectSelectionList(listIdentifier):
    currentList = cmds.textScrollList(listIdentifier, query=True, allItems=True)
    selection = cmds.ls(selection=True)
    for obj in selection:
        if not isinstance(currentList, list) or obj not in currentList:
            cmds.textScrollList(listIdentifier, edit=True, append=obj)
        
def removeFromObjectSelectionList(listIdentifier):
    listSelection = cmds.textScrollList(listIdentifier, query=True, selectItem=True)
    
    if listSelection != None:
        for listObject in listSelection:
            cmds.textScrollList(listIdentifier, edit=True, removeItem=listObject)
    
def addObjectSelectionList(listIdentifier, label):
    cmds.columnLayout(adjustableColumn=True)
    cmds.rowLayout(columnAttach3=['left', 'left', 'right'], numberOfColumns=3, adjustableColumn=3, columnWidth3=[10, 30, 100])
    cmds.iconTextButton(listIdentifier, style='iconOnly', image1='addClip.png', width=22, height=22, command='addToObjectSelectionList("'+listIdentifier+'")')
    cmds.iconTextButton(style='iconOnly', image1='trash.png', width=22, height=22, command='removeFromObjectSelectionList("'+listIdentifier+'")')
    cmds.text(label=label)
    parentToLayout()
    
    scrollList = cmds.textScrollList(listIdentifier, allowMultiSelection=True, height=90)
    parentToLayout()
    return scrollList

# File Browser

# 0     Any file, whether it exists or not.
# 1     A single existing file.
# 2     The name of a directory. Both directories and files are displayed in the dialog.
# 3     The name of a directory. Only directories are displayed in the dialog.
# 4     Then names of one or more existing files.

def browseForDirectory(identifier, mode):
    mode = int(mode)
    path = cmds.fileDialog2(fileMode=mode)
    cmds.textField(identifier, edit=True, text=path[0])

def addFileBrowser(identifier, mode, placeholderText, defaultText):
    cmds.rowLayout(numberOfColumns=2, columnAttach=[(1, 'left', 0), (2, 'right', 0)], adjustableColumn=1, height=22)
    textFieldControl = cmds.textField(identifier, placeholderText=placeholderText, text=defaultText)
    cmds.iconTextButton(style='iconOnly', image1='browseFolder.png', label='spotlight', command='browseForDirectory("'+identifier+'", '+str(mode)+')')
    cmds.setParent("..")
    return textFieldControl;

def newOptionMenu(identifier, label, cc=None):
    cmds.optionMenu(str(identifier), label=str(label), cc=str(cc))

def addMenuItem(identifier, label):
    cmds.menuItem(identifier, label=label)

def addOptionMenu(identifier:str,label:str,menuitems=["1","2","3"],cc=None):
    cmds.optionMenu(identifier, label=str(label),cc=str(cc))
    for i in menuitems:
        cmds.menuItem(label=str(i))
                    
def deleteIfOpen():  
    if cmds.window('windowObject', exists=True):
        cmds.deleteUI('windowObject')
        
def getCloseCommand():
    return('cmds.deleteUI(\"' + 'windowObject' + '\", window=True)')

def createWindow():
    cmds.window(
        'windowObject', 
        title=WINDOW_TITLE, 
        width=WINDOW_WIDTH,
        height=100,
        maximizeButton=False,
        resizeToFitChildren=True
    )
    addSpacer()
    addHeader('Call of Duty Map Importer')
    addText('Importer for Call of Duty maps')
    cmds.text(label='<span style=\"color:#ccc;text-decoration:none;font-size:px;font-family:courier new;font-weight:bold;\">' + "Created by <a href=\"https://twitter.com/MrChuse\" style=\"color:purple\"> MrChuse</a>" + '</span>', hyperlink=True)
    addSpacer()
        
    addFrameColumnLayout('Import Settings', False)

    addDoubleRowLayout()
    addText('Game: ')
    addOptionMenu("game","", ["Modern Warfare 2019", "Other"])
    parentToLayout()
    addDoubleRowLayout()
    addText('Map File: ')
    addFileBrowser("mapFile", 1, 'Test placeholder text', 'Select Map File')
    parentToLayout()
    addDoubleRowLayout()
    addText('OBJ File: ')
    addFileBrowser("OBJFile", 1, 'Test placeholder text', 'Select OBJ File')
    parentToLayout()
    

    addDoubleRowLayout()
    # addSpacer()
    addText('XModels Folder: ')
    addFileBrowser("xmodels_folder", 3, 'Test placeholder text', 'Select XModels Folder')
    parentToLayout()


    addDoubleRowLayout()
    addSpacer()
    addCheckbox("use_bbox", 'Use Bounding Box')
    parentToLayout()
    
    addDoubleRowLayout()
    addSpacer()
    addCheckbox("disable_viewport", 'Disable Viewport')
    parentToLayout()

    addDoubleRowLayout()
    addSpacer()
    addCheckbox("abc_export", 'Export an Alembic File')
    parentToLayout()

    addButton( 'Start', "Main()")

    addFrameColumnLayout('Other Functions', True)

    # addDoubleRowLayout()
    addSpacer()
    addButton('Create Model List', "MakeModelList()")
    addButton('Create OBJ Material List', "TextureList4Mats()")
    parentToLayout()
    
    cmds.showWindow('windowObject')
deleteIfOpen()
createWindow()