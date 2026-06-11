#####################################################
module_path='' #With trailing slash 
#####################################################
import sys
if module_path + 'ReferenceReconstructionAndNLTFM' not in sys.path: 
	sys.path.append(module_path+'ReferenceReconstructionAndNLTFM')
if module_path +'ReferenceReconstructionAndNLTFM/TFR_Python' not in sys.path: 
	sys.path.append(module_path+'ReferenceReconstructionAndNLTFM/TFR_Python')
if '../'+ module_path +version not in sys.path: 
	sys.path.append('../'+ module_path+'ReferenceReconstructionAndNLTFM')
if '../'+ module_path +'ReferenceReconstructionAndNLTFM/TFR_Python' not in sys.path: 
	sys.path.append('../'+ module_path+'ReferenceReconstructionAndNLTFM/TFR_Python')
######################################################
import TFR_Python
######################################################



######################################################
# 					User Inputs 					 #
UI={}

UI['job_name']=''
UI['z_constr']=True
UI['BaseModelPath']='BaseModel/BaseModel_9-10_6.10EF1.cae'

UI['relative_threshold']=True
UI['threshold']=0.35
UI['refined_mesh_size']=0.3

UI['CPUs']=8

######################################################

TFR=TFR_Python.TractionForceReconstruction(UI)
TFR.ReadInputData()
TFR.AdaptiveMesh()
TFR.BCApplication()
TFR.CreateJob()
TFR.Save()
TFR.ExportMeshData()
TFR.Run()
TFR.ExportResults()
TFR.Save()
TFR.Alert()

