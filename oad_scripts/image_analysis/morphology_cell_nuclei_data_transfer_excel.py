"""
File: morphology_cell_nuclei_data_transfer_excel.czmac
Author: SRh + CSc
Date: 2017_05_19
Version: 0.2

Macro name: Morphology of cell nuclei and data transfer to Excel
Required files:
- morphology_of_nuclei.czi
- morphology_cell_nuclei.czias

LOAD IMAGE, SEGMENT NUCLEI, MEASURE SIZE OF NUCLEI
SEND DATA TO EXCEL AND GENERATE DATALIST AND CHART 
"""

import clr
clr.AddReferenceByName('Microsoft.Office.Interop.Excel, Version=11.0.0.0, Culture=neutral, PublicKeyToken=71e9bce111e9429c')
from Microsoft.Office.Interop import Excel
excel = Excel.ApplicationClass()
from System.IO import Directory, Path, File, FileInfo

showexcel = True

# clear output console
Zen.Application.MacroEditor.ClearMessages()

testimage = r'c:\Users\M1SRH\Documents\Testdata_Zeiss\OAD_Testimages\morphology_of_nuclei.czi'
czias = r'c:\Users\M1SRH\Documents\Testdata_Zeiss\OAD_Testimages\morphology_cell_nuclei.czias'
basepath = Path.GetDirectoryName(testimage)

print 'Testimage  : ', testimage
print 'CZIAS File : ', czias

# load the image automatically
image = Zen.Application.LoadImage(testimage)
Zen.Application.Documents.Add(image)
# Set channel color for DAPI (optional)
image.SetChannelColor(0,ZenColors.LightBlue)

# load image analysis setting (CZIAS) and run
print 'Run CZIAS on loaded image ...'
ias=ZenImageAnalysisSetting()
ias.Load(czias)
Zen.Analyzing.Analyze(image, ias)

# lreate data list with results for single objects
regTable = Zen.Analyzing.CreateRegionTable(image)
Zen.Application.Documents.Add(regTable)

# save results as CSV file
regTableName = regTable.Name
regTable.Save(Path.Combine(basepath, regTable.Name + '.csv'))

# transfer data to Excel
if showexcel:
    
    print 'Transfer data to Excel ...'
    excel.Visible = True
    excel.DisplayAlerts = False
    
    workbook = excel.Workbooks.Add()
    worksheet = workbook.Worksheets[1]
    
    excel.Cells(1,1).Value = 'Region ID'
    excel.Cells(1,2).Value = 'Area[µm2]'
    excel.Cells(1,3).Value = 'Form Cicle'
    excel.Cells(1,4).Value = 'FeretRatio'
    excel.Cells(1,5).Value = 'Ellipse Angle[°]'
    excel.Cells(1,6).Value = 'Ellipse Major[µm2]'
    excel.Cells(1,7).Value = 'Ellipse Minor[µm2]'
    
    for Row in range(0,regTable.RowCount):
        for Col in range(0,regTable.ColumnCount):
            excel.Cells(Row+2,Col+1).Value = regTable.GetValue(Row,Col)
    
    xlLine = 4
    msoFalse = 0
    msoScaleFromTopLeft = 0
    
    excel.Cells.Select()
    excel.Cells.EntireColumn.AutoFit()
    excel.Rows('1:1').Select()
    excel.Selection.Font.Bold = True
    excel.Range('A1').Select
    excel.ActiveSheet.Shapes.AddChart().Select()
    excel.ActiveChart.ChartType = xlLine
    
    try:
        excel.ActiveChart.SetSourceData(excel.Range('Tabelle1!$A$1:$G$32'))
    except:
        excel.ActiveChart.SetSourceData(excel.Range('Sheet1!$A$1:$G$32'))
    
    ActiveShape = excel.ActiveSheet.Shapes(excel.ActiveSheet.Shapes.Count)
    ActiveShape.Left = 500
    ActiveShape.Top = 50
    ActiveShape.ScaleWidth(1.45, msoFalse, msoScaleFromTopLeft)
    ActiveShape.ScaleHeight(1.85, msoFalse, msoScaleFromTopLeft)
    excel.Range("A1").Select()

print 'Done.'
