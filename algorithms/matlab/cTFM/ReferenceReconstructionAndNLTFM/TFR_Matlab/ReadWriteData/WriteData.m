%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%                                                                                   %
%                             Copyright (c) 2014-2015                               %
%				      Manuel Zündel (zuendel@imes.mavt.ethz.ch)                     %
%                       Alexander E. Ehret and Edoardo Mazza                        %
%				       Experimental Continuum Mechanics Group                       %
%				    Institute of Mechanical Systems, ETH Zürich                     %
%				                All rights reserved.                                %
%                                                                                   %
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%


function  WriteData( UI,measurementData,DotCoords0 )
% Writes the data in textfiles for the NonLinear TFM part

WritePath='PreparedData/';
if exist(WritePath)~=7
    mkdir(WritePath);
end

dlmwrite(strcat(WritePath,strcat(UI.parameters.job_name,'_triangles.txt')),measurementData.Triangles-1,'delimiter','\t','newline','pc');
dlmwrite(strcat(WritePath,strcat(UI.parameters.job_name,'_points.txt')),DotCoords0,'delimiter','\t','newline','pc');
dlmwrite(strcat(WritePath,strcat(UI.parameters.job_name,'_displacement.txt')),measurementData.DotCoords-DotCoords0,'delimiter','\t','newline','pc');


image_scaling=measurementData.image_scaling;
dot_distance=measurementData.dot_distance;
ImageSize=measurementData.ImageSize;

save(strcat(WritePath,strcat(UI.parameters.job_name,'_UserData')),'image_scaling','dot_distance','ImageSize');
dlmwrite(strcat(WritePath,strcat(UI.parameters.job_name,'_UserDataABQ.txt')),[image_scaling dot_distance ImageSize],'delimiter','\t','newline','pc');



display('Data has been exported for Abaqus!')


end

