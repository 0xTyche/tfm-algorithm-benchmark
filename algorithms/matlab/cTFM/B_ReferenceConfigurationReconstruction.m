clc; clear all; close all;
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%                                                                         %
%            cTFM:       Reference Position Reconstruction                %
%                                                                         %
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
module_path=''; % With trailing slash
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%


%% User Input

% Path to Input Data
path_data='';
% Job Name
job_name='';

fixed_frame= 2; % Distance (in micrometers) from the frame of the fixed dots
N_max=10000; % Maximal Number of Iterations for the Optimization
Relative_threshold=1e-6; % Minimal relative decrease of fitness to continue optimization 
plotUpdatedQDMesh=1; % Plot Updated QD mesh during optimization process ( 0 or 1)


% Bundle user Input in structure
paths_data=struct('Data',path_data);
parameters=struct('fixed_frame', fixed_frame,'N_max',N_max,'Relative_threshold',Relative_threshold,'job_name',job_name);
user_input=struct('Paths', paths_data,'parameters',parameters);

%% Run Reconstruction

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Load all scripts
run(strcat(module_path,'ReferenceReconstructionAndNLTFM/TFR_Matlab/LoadAll.m'));
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% Import measured data
measurementData=LoadData(user_input);


% Compute Initial Dot Position
DotCoords0=ComputeInitialPosition(user_input, measurementData ,plotUpdatedQDMesh);

% Write Data to Textfiles
WriteData(user_input,measurementData,DotCoords0)
