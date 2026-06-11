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


function [ Data,used_points ] =LoadData( UI,Move,FlipUD)
% Loads the data about the grid and the triangles
    
    % Set default arguments
    if nargin < 2
      Move=0;
    end
    
    if nargin < 3
      FlipUD=1;
    end

    % Load deformed QD Data from .mat file
    griddata= load(UI.Paths.Data);
    scale_factor=griddata.factor;
    triangles=griddata.triangles;
    
    % Scale x,y and if available also z coordinates from pixel to um
    griddata.xcoords=griddata.xcoords*scale_factor;
    griddata.ycoords=griddata.ycoords*scale_factor;
    
    if isfield(griddata,'zcoords')==0
        griddata.zcoords=zeros(length(griddata.ycoords),1);
    else
        griddata.zcoords=griddata.zcoords*scale_factor;
    end
    
    % Get microscopy image size
    Image_size=size(griddata.img);
    
    % If requested, flip the coordinate system upside-down, so that plots and microscopy image have the same orientation
    if FlipUD==1
        griddata.ycoords=Image_size(1)*scale_factor-griddata.ycoords;
        
    end
    
    
    % If requested, Move Coordinate System to the image center
    
    if Move==1  
        griddata.xcoords=griddata.xcoords-Image_size(2)/2*scale_factor;
        griddata.ycoords=griddata.ycoords-Image_size(1)/2*scale_factor;
        
    end
    
    % eliminate unused points and triangles
    triangles_=triangles;
    used_points=[];
    DotCoords=[];
    k=1;
    for i=1:length(griddata.xcoords)
        if length(find(triangles == i))==0
            col=find(triangles > i);
            triangles_(col)=triangles_(col)-1;
        else
            used_points(k)=i;
            DotCoords(k,:)=[griddata.xcoords(i),griddata.ycoords(i),griddata.zcoords(i)];
            k=k+1;
        end
    end
    triangles=triangles_;
    
    
    % Save Data in Structure
    Data=struct('DotCoords',DotCoords,'Triangles',triangles, 'image_scaling', scale_factor,'dot_distance', griddata.pitch , 'ImageSize' , Image_size);
    
    % Print Status
    display('Experimental Data has been read!')
    display(strcat(int2str(length(DotCoords(:,1))),' Dots and ',{' '}, int2str(length(triangles(:,1))),' Triangles have been found!'))
    
    display(['The BaseModel Size should be at least ' num2str(ceil(Image_size(2)*scale_factor)) 'x' num2str(ceil(Image_size(1)*scale_factor)) ' micrometers.' ])
end

