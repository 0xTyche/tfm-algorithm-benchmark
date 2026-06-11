%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% f_imaris_import is called by the cTFM mesh generator                    %
%                                                                         %
% This function takes loads the 3D coordinates from an imaris export and  %
% does a tilt correction to account for skewness between the focal and    %
% substrate plane.                                                        %
%                                                                         %
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
function [x,y,z] = f_imaris_import(csvname, csvpath)
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%add path for functions not created by me
addpath('functions\affine_fit');
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

[pathstr,name,ext] = fileparts(csvname);
if strcmp(ext,'.xls') || strcmp(ext,'.xlsx')
    %-------xlsx read--------------------------
    [pos,~,~] = xlsread([csvpath,'\',csvname],'Position');
elseif strcmp(ext,'.csv')
    %-------csv read---------------------------
    fid = fopen([csvpath,'\',csvname]);
    out = textscan(fid,'%f %f %f %s %s %s %s %s','delimiter',',','HeaderLines',4); %0.067,1.31803,2.13031,um,Spot,Position,1,0,

    fclose(fid);

    pos(:,1) = out{1};
    pos(:,2) = out{2};
    pos(:,3) = out{3};
    %-------end read--------------------------
end


%load('Imaris_pos.mat')

x = pos(:,1);
y = pos(:,2);
z = pos(:,3);

% %flip z if stack was imaged from top to bottom!!!
% zmax =max(z);
% z = -z+zmax;

%fitting plane for tilt correction
z_lowerlimit = 0;
[~,V,p] = affine_fit([x(z>z_lowerlimit),y(z>z_lowerlimit),z(z>z_lowerlimit)]);

%solving plane equation for fine grid
s = (y-p(2)-(x-p(1))*V(2,1)/V(1,1))/(V(2,2)-V(1,2)/V(1,1)*V(2,1));
t = (x-p(1)-s*V(1,2))/V(1,1);
z_plane = p(3) + t * V(3,1) + s * V(3,2);

z = (z - z_plane);