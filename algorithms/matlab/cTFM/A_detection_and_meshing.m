clc; close all; clear all;
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% This is the first step in the cTFM. It starts the cTFM meshing GUI      %
%                                                                         %
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

if isunix
    cd('../cTFM_Framework/Detection_Meshing')
else
    cd('..\cTFM_Framework\Detection_Meshing')
end
cTFM_meshing