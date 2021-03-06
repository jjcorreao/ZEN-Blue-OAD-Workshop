"""
Author: Sebastian Rhode
Date: 2017_08_06
File: Guided_Acquistion_DLLs.czmac
Version: 4.3

Optimized for the use with Celldiscoverer 7 and DF2, but applicable for all motorized stands ruuning in ZEN Blue
Please adapt Focussing commands, especially FindSurface when using with other stands

1) - Select Overview Scan Experiment
2) - Select appropriate Image Analysis Pipeline
3) - Select Detailed Scan Experiment
4) - Specify the output folder for the image and data tables

Requires the following DLLs to be found inside the Zen program folder:

- RETools.dll
- TileTools.dll
"""

# import DLLs
import clr
clr.AddReference('RETools.dll')
clr.AddReference('TileTools.dll')
import RETools
import Tiles
import time
from datetime import datetime
import errno

from System.IO import File, Directory, Path
import sys

# optional debugging output
verbose = True
# version number for dialog window
version = 4.3
# file name for overview scan
ovscan_name = 'OverviewScan.czi'
# additional XY offest for possible LSM port relative to the Camera port (zero)
dx_LSM = 0.0
dy_LSM = 0.0

def dircheck(basefolder):

    # check if the destination basefolder exists
    base_exists = Directory.Exists(basefolder)
    if base_exists:
        # specify the desired output format for the folder, e.g. 2017-08-08_17-47-41
        format = '%Y-%m-%d_%H-%M-%S'
        # create the new directory
        newdir = createfolder(basefolder, formatstring=format)
        print 'Created new directory: ', newdir

    return newdir


def createfolder(basedir, formatstring='%Y-%m-%d_%H-%M-%S'):
    # construct new directoty name nased on date and time
    newdir = Path.Combine(basedir, datetime.now().strftime(formatstring))
    # check if the new directory (for whatever reasons) already exists
    try:
        newdir_exists = Directory.Exists(newdir)
        if not newdir_exists:
            # create new directory if is does not exist
            Directory.CreateDirectory(newdir)
        if newdir_exists:
            # raise error if it really already exists
            raise SystemExit
    except OSError as e:
        if e.errno != errno.EEXIST:
            newdir = None
            raise  # This was not a "directory exist" error..

    return newdir

# clear console output
Zen.Application.MacroEditor.ClearMessages()

# check the location of folder where experiment setups and image analysis settings are stored
docfolder =  Zen.Application.Environment.GetFolderPath(ZenSpecialFolder.UserDocuments)
#imgfolder =  Zen.Application.Environment.GetFolderPath(ZenSpecialFolder.ImageAutoSave)
imgfolder = r'c:\Output\Guided_Acquistion'
format = '%Y-%m-%d_%H-%M-%S'

# get list with all existing experiments and image analysis setup
expfiles = RETools.RareEventTools.GetExperimentSetups(docfolder)
ipfiles = RETools.RareEventTools.GetImageAnalysisSetups(docfolder)

# collect information about the configured objectives and optovars
objectives = RETools.RareEventTools.CreateObjectiveInfo()
optovars = RETools.RareEventTools.CreateOptovarInfo()
if verbose:
    print('Objectives:')
    print('Number: ', objectives.Count)
    print('Names: ', objectives.Names)
    print('Positions: ', objectives.Positions)
    print('-------------------------------------------')
    print('Optovars:')
    print('Number: ', optovars.Count)
    print('Names: ', optovars.Names)
    print('Positions: ', optovars.Positions)
    print('\n')

# Activate Zen.Application
RareEventDialog = ZenWindow()
RareEventDialog.Initialize('Guided Acquisition - Version : ' + str(version), 650, 750, True, True)
# add components to dialog
RareEventDialog.AddLabel('1) Select Overview Experiment  ------------------------------')
RareEventDialog.AddDropDown('overview_exp', 'Overview Scan Experiment', expfiles, 0)
RareEventDialog.AddDropDown('objectiveOV', 'Objective OvervIew Scan', objectives.Names, 1)
RareEventDialog.AddDropDown('optovarOV', 'After-Mag OverViewScan', optovars.Names, 2)
RareEventDialog.AddCheckbox('SWAF_before_overview', 'OPTION - (Find Surface) & SWAF before Overview', True)
RareEventDialog.AddLabel('2) Select Image Analysis to detect objects  -----------------')
RareEventDialog.AddDropDown('ip_pipe', 'Image Analysis Pieline', ipfiles, 0)
RareEventDialog.AddLabel('3) Select Detail Scan Experiment  ---------------------------')
RareEventDialog.AddDropDown('detailed_exp', 'Detailed Scan Experiment', expfiles, 1)
RareEventDialog.AddDropDown('objectiveDT', 'Objective Detailed Scan', objectives.Names, 2)
RareEventDialog.AddDropDown('optovarDT', 'After-Mag Detailed Scan', optovars.Names, 2)
RareEventDialog.AddCheckbox('checkoffset', 'OPTION - Check offset between FS and SWAF', False)
RareEventDialog.AddCheckbox('manualoffset', 'OPTION - Enter Offset manually', False)
RareEventDialog.AddDoubleRange('offsetvalue', 'Enter manual Offset [micron]', 0, 0, 100)
RareEventDialog.AddLabel('4) Specify Output Folder to save the images -----------------')
RareEventDialog.AddFolderBrowser('outfolder','Output Folder for Images and Data Tables', imgfolder)

# show the window
result = RareEventDialog.Show()
if result.HasCanceled:
    message = 'Macro was canceled by user.'
    print message
    raise SystemExit

# get the values and store them
OverViewExpName = str(result.GetValue('overview_exp'))
ImageAS = str(result.GetValue('ip_pipe'))
DetailExpName = str(result.GetValue('detailed_exp'))
OutputFolder = str(result.GetValue('outfolder'))
SWAF_beforeOV = result.GetValue('SWAF_before_overview')
CheckOffset = result.GetValue('checkoffset')
ManualOffset = result.GetValue('manualoffset')
OffsetValue = result.GetValue('offsetvalue')
objOV = result.GetValue('objectiveOV')
optoOV = result.GetValue('optovarOV')
objDT = result.GetValue('objectiveDT')
optoDT = result.GetValue('optovarDT')

# print values - this is optional
print 'Overview Scan Experiment : ' + OverViewExpName
print 'Combination OverView Scan: ', objOV + ' + ' + optoOV
print 'Image Analysis Pipeline : ' + ImageAS
print 'Detailed Scan Experiment : ' + DetailExpName
print 'Combination Detailed Scan: ', objDT + ' + ' + optoDT
print 'Output Folder for Data : ' + OutputFolder, '\n'

# check directory
OutputFolder = dircheck(OutputFolder)

# check Detail Scan experiment for tiles
DetailScan = Zen.Acquisition.Experiments.GetByName(DetailExpName)
DetailScan.SetActive()
DetailIsTileExp = Tiles.TileTools.IsTilesExperiment(DetailScan)
DetailScan.Close()

# check Overview Scan for tiles
OVScan = Zen.Acquisition.Experiments.GetByName(OverViewExpName)
OVScan.SetActive()
OVScanIsTileExp = Tiles.TileTools.IsTilesExperiment(OVScan)

if (OVScanIsTileExp == False or DetailIsTileExp == False):
    message = 'Overview or Detail Scan are not a Tile Experiment.'
    print message
    raise SystemExit
    OVScan.Close()

############# START OVERVIEW SCAN EXPERIMENT #################

# use the correct objective and optovar for the overview scan
RETools.RareEventTools.SetObjOptovarbyName(objOV, optoOV, False, False)

if SWAF_beforeOV==True:
    try:
        # initial focussing via FindSurface to assure a good starting position
        # requires DF2 for Obsever or Celldiscoverer 7 --> otherwise comment line !!!
        Zen.Acquisition.FindSurface()
    except:
        print 'Was not able to run Find Surface.'

    try:
        # run the SWAF using the settings from the OVScan --> check SWAF  for overview experiment !!!
        Zen.Acquisition.FindAutofocus(OVScan)
    except:
        print 'Was not able to run SWAF using the seetings: ', OverViewExpName

# get the resulting z-position
znew = Zen.Devices.Focus.ActualPosition

# try to adapt the Tile Experiment with new Z-Position
try:
    Tiles.TileTools.ModifyTileRegionsZonly(OVScan, znew)
    print 'Adapted Z-Position of Tile OverView. New Z = ',znew
except:
    print 'Was not able to adapt Z-Position of Overview Scan Experiment.'

# execute the experiment
print 'Running OverviewScan Experiment.\n'
output_OVScan = Zen.Acquisition.Execute(OVScan)
OVScan.Close()
# For testing purposes - Load overview scan image automatically instead of executing the "real" experiment
#output_OVScan = Zen.Application.LoadImage(r'c:\Users\M1SRH\Documents\Testdata_Zeiss\RareEvent_Test_Wizard\OverViewScan_Test_raw.czi', False

# show the overview scan inside the document area
Zen.Application.Documents.Add(output_OVScan)
ovdoc = Zen.Application.Documents.GetByName(output_OVScan.Name)

# save the overview scan image inside the select folder
output_OVScan.Save(OutputFolder + '\\' + ovscan_name)

############# END OVERVIEW SCAN EXPERIMENT ###################

# Load analysis setting created by the wizard or an separate macro
ias = ZenImageAnalysisSetting()
# for simulation use: 000 - RareEventExample.czias
ias.Load(ImageAS)
# Analyse the image
Zen.Analyzing.Analyze(output_OVScan,ias)
# Create Zen table with results for all detected objects (parent class)
AllObj = Zen.Analyzing.CreateRegionsTable(output_OVScan)
# Create Zen table with results for each single object
SingleObj = Zen.Analyzing.CreateRegionTable(output_OVScan)

# check for existence of required column names
DetailScan = Zen.Acquisition.Experiments.GetByName(DetailExpName)
DetailScan.SetActive()
DetailIsTileExp = Tiles.TileTools.IsTilesExperiment(DetailScan)
out =  RETools.RareEventTools.CheckColumns(SingleObj, DetailIsTileExp)
DetailScan.Close()

# 1st item is a bool indicating if all required columns could be found
columnsOK = out.Item1

if columnsOK == False:
    print 'Execution stopped. Required Columns are missing.'
    raise Exception('Execution stopped. Required Columns are missing.')

# 2nd item is a dictionary containing the tile properties
# colID: used keys = 'BCcolx' / 'BCcoly' / 'BCWidthcolx' / 'BCHeightcoly'
colID = out.Item2

# show and save data tables to the specified folder
Zen.Application.Documents.Add(AllObj)
Zen.Application.Documents.Add(SingleObj)
AllObj.Save(OutputFolder + '\\OverviewTable.csv')
SingleObj.Save(OutputFolder + '\\SingleObjectsTable.csv')

# check the number of detected objects = rows inside image analysis table
num_POI = SingleObj.RowCount

# switch to new magnification and optovar before the detailed scan starts
RETools.RareEventTools.SetObjOptovarbyName(objDT, optoDT, False, False)

# determine offset between FindSurface and objects found by SWAF --> required DF2
if CheckOffset==True:
    # move to the first valid XY position to detemine the offset
    xpos_1st   = SingleObj.GetValue(0, colID['BCcolx']) # get x stage position from list
    ypos_1st   = SingleObj.GetValue(0, colID['BCcoly']) # get y stage position from list
    Zen.Devices.Stage.MoveTo(xpos_1st + dx_LSM, ypos_1st + dy_LSM)

    # get the actual offset using FindSurface followed by SWAF --> requires DF2
    try:
        dzFS = RETools.RareEventTools.getOffsetFindSurfaceSWAF(DetailExpName, False)
        print 'Automatic Offset dzFS measured [micron]: ', round(dzFS, 2)
        # store this new value inside the DF in order to use RecallFocus later on
        print 'Store Z-Value Offset for RecallFocus.\n '
        # store offset inside DF to use it with Recall Focus using DF2
        Zen.Acquisition.StoreFocus()
        useRecallFocus = True
    except:
        print 'Automatic Offset Check failed. Setting Offset dzFS = 0.'
        dzFS = 0.0
        useRecallFocus = False

elif CheckOffset==False:
    dzFS = 0.0
    useRecallFocus = False

if ManualOffset==True and CheckOffset==False:
    # use the manually entered offset only when dz was not measured automatically
    dzFS = OffsetValue
    print ' Manual Offset [micron]: ', round(dzFS, 2)

# wait just to be sure everything is finished
time.sleep(2)

############# START DETAILED SCAN EXPERIMENT #############

# execute detailed experiment at the position of every detected object
for i in range(0, num_POI, 1):

    # get the object information from the position table
    POI_ID = SingleObj.GetValue(i, 0) # get the ID of the object - IDs start with 2 !!!
    xpos = SingleObj.GetValue(i, colID['BCcolx']) # get X-stage position from table
    ypos = SingleObj.GetValue(i, colID['BCcoly']) # get Y-stage position from table

    # move to the current position
    Zen.Devices.Stage.MoveTo(xpos + dx_LSM, ypos + dy_LSM) # comment this, if one uses a simulated experiment
    print 'Moving Stage to Object ID:', POI_ID, ' at :', round(xpos, 2), round(ypos, 2)

    if useRecallFocus == False:
        # Initial FindSurface before the Detail Scan starts
        try:
            Zen.Acquisition.FindSurface()
        except:
            'Was not able to run Find Surface.'
        # calculate new focus position plus offset and move z-drive
        zpos = Zen.Devices.Focus.ActualPosition + dzFS
        print 'Move to Z-Position: ', round(zpos, 2)
        Zen.Devices.Focus.MoveTo(zpos)

    elif useRecallFocus == True:
        # alternative solution - use RecallFocus
        try:
            Zen.Acquisition.RecallFocus()
        except:
            print 'Was not able to run Recall Focus.'
        zpos = Zen.Devices.Focus.ActualPosition
        print 'New z-position after Recall Focus: ', zpos

    # load the predefined detailed scan experiment
    DetailScan = Zen.Acquisition.Experiments.GetByName(DetailExpName)

    # only modify the Tile Properties if required IAS features BoundWidth and BoundHeight were found
    # if experiment is a Tile Experiment
    if DetailIsTileExp == True:

        # Modify tile center position - get bounding rectangle width & height in microns
        bcwidth =  SingleObj.GetValue(i, colID['BCWidthcolx'])
        bcheight = SingleObj.GetValue(i, colID['BCHeightcoly'])
        print 'Width and Height : ', str(round(bcwidth, 2)), str(round(bcheight, 2))
        print 'Modifying Tile Properties XYZ Position and width & height.'
        # Modify the XYZ position of the tile region on-the-fly
        Tiles.TileTools.ModifyTileRegionsXYZ(DetailScan, xpos, ypos, zpos)
        # Modify ConturSize for the tile according to the size of the bounding rectangle
        Tiles.TileTools.ModifyTileRegionsSize(DetailScan, bcwidth, bcheight)
        print 'New Tile Properties: ', round(xpos, 2), round(ypos, 2), round(zpos, 2), round(bcwidth, 2), round(bcheight, 2)

    # execute the experiment
    print 'Running Detail Scan Experiment at new XYZ position.'

    # run the Detail Scan
    output_detailscan = Zen.Acquisition.Execute(DetailScan)
    DetailScan.Close()

    # get the image data name
    dtscan_name = output_detailscan.Name
    # save the image data to the selected folder and close the image
    output_detailscan.Save(OutputFolder + '\\' + output_detailscan.Name)
    output_detailscan.Close()
    # rename the CZI regarding to the object ID - Attention - IDs start with 2 !!!
    newname_dtscan = 'DTScan_ID' + str(POI_ID) + '.czi'
    if verbose:
        print 'Renaming File: ' + dtscan_name + ' to: ' + newname_dtscan + '\n'
    File.Move(OutputFolder + '\\' + dtscan_name, OutputFolder + '\\' + newname_dtscan)

############# END DETAILED SCAN EXPERIMENT #############

# show the overview scan document again at the end
Zen.Application.Documents.ActiveDocument = ovdoc
print 'All Positions done. RareEvent Detection finished.'
