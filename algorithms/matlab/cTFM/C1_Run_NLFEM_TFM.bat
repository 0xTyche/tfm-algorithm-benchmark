if not exist Temp mkdir Temp
cd Temp
del abaqus.rpy.*
abaqus cae script=../C1_NLFEM_TFM.py noStartupDialog
cd '../'