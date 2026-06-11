%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% f_save is called by the cTFM mesh generator               %
%                                                           %
% This function handles the saving of data acquired by the  %
% GUI. Depending on the input it will save the nodes or     %
% mesh.                                                     %
%                                                           %
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

function pass = f_save(handles,sCase)
clear data
switch sCase
    case 'nodes'
        if isfield(handles.var,'xcoords')
            data.xcoords = handles.var.xcoords;
            data.ycoords = handles.var.ycoords;
            if isfield(handles.var,'zcoords')
                data.zcoords = handles.var.zcoords;
            end
            data.threshold = handles.var.threshold;
            data.KDTree = handles.var.KDTree;
        else
            pass = 'Node coordinates not available';
            return;
        end
    case 'mesh'
        if isfield(handles.var,'hex_index')
            data.hex_index = handles.var.hex_index;
            data.hex_distance = handles.var.hex_distance;
            data.groups = handles.var.groups;
            data.clusters = handles.var.clusters;
            data.factor = handles.var.factor;
            data.pitch = handles.var.pitch;
            data.dist_error = handles.var.dist_error;
            data.angle_error = handles.var.angle_error;
            try
                data.manual_conn = handles.var.manual_conn;
            end
        else
            pass = 'Mesh data not fully available';
            return;
        end
    case 'strain'
        if isfield(handles.var,'strain')
            data.max_EVal = handles.var.max_EVal;
            data.strain = handles.var.strain;
            data.triangles = handles.var.triangles;
            data.F =  handles.var.F;
            data.E =  handles.var.E;
        else
            pass = 'Strain not available';
        end
    case 'stress'
        if isfield(handles.var,'stress')
            data.stress = handles.var.stress;
            data.sigma = handles.var.sigma;
        else
            pass = 'Stress not available';
        end        
    otherwise
        pass = 'Invalid sCase in f_save.m';
        return;
end
check = f_savecheck(handles.var,sCase);

if check == 0
    % 'sCase'.mat already exists
    choice = questdlg([sCase,'.mat already exists. Overwrite?'], ...
        'Overwrite?', ...
        'Overwrite','Save as...','Cancel','Cancel');
    % Handle response
    switch choice
        case 'Overwrite'
            save([handles.var.ImageFolder,'/',handles.var.ImageName,'/',sCase,'.mat'],'data')
        case 'Save as...'
            uisave({'data'},[sCase,'.mat']);                
        case 'Cancel'
            
    end
    pass = 1;
    return;
elseif check == -1
    pass = 'Error occured. f_savecheck used with invalid input.';
else
    save([handles.var.ImageFolder,'/',handles.var.ImageName,'/',sCase,'.mat'],'data')
    pass = 1;
end