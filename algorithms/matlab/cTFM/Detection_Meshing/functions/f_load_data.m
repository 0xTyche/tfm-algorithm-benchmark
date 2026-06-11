%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% f_load_data is called by the cTFM mesh generator          %
%                                                           %
% This function can either check the availability of data   %
% or is used to load all available data for the current     %
% image.                                                    %
%                                                           %
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

function [sReturn,handles] = f_load_data(handles,sCase)
var = handles.var;
[~,dir,dir2]=fileparts(var.ImageName);
switch sCase
    case 'load'
        disp('Loading available TFM data')
        if exist([var.ImageFolder,'/',var.ImageName,'/nodes.mat'],'file')==2
            load([var.ImageFolder,'/',var.ImageName,'/nodes.mat'])
            %load([var.ImageFolder,'/',var.ImageName,'/nodes_w_z.mat'])
            sReturn.xcoords = data.xcoords;
            sReturn.ycoords = data.ycoords;
            try
                sReturn.zcoords = data.zcoords;
                set(handles.ctfm_disp_nodes3D,'Enable','on')
            end
            sReturn.threshold = data.threshold;
            sReturn.KDTree = data.KDTree;
            set(handles.ctfm_disp_nodes,'Enable','on')
            set(handles.ctfm_pbt_mesh,'Enable','on')
            set(handles.ctfm_pbt_detect_add,'Enable','on')
            set(handles.ctfm_pbt_detect_delete,'Enable','on')
            set(handles.ctfm_pbt_detect_save,'Enable','on')

        end
        if exist([var.ImageFolder,'/',var.ImageName,'/mesh.mat'],'file')==2
            load([var.ImageFolder,'/',var.ImageName,'/mesh.mat'])
            sReturn.hex_index = data.hex_index;
            sReturn.factor = data.factor;
            sReturn.pitch = data.pitch;
            try
                sReturn.manual_conn = data.manual_conn;
            end
            try
                sReturn.angle_error = data.angle_error;
                sReturn.dist_error = data.dist_error;
            end
            set(handles.ctfm_disp_mesh,'Enable','on')

            set(handles.ctfm_pbt_mesh_add,'Enable','on')
            set(handles.ctfm_pbt_mesh_delete,'Enable','on')
            set(handles.ctfm_pbt_mesh_save,'Enable','on')
        end
        if exist([var.ImageFolder,'/',var.ImageName,'/strain.mat'],'file')==2
            load([var.ImageFolder,'/',var.ImageName,'/strain.mat'])
            sReturn.strain = data.strain;
            try
                sReturn.triangles = data.triangles;
            end
            try
                sReturn.F = data.F;
                sReturn.E = data.E;
            end
            set(handles.disp_strain,'Enable','on')
        end
        if exist([var.ImageFolder,'/',var.ImageName,'/stress.mat'],'file')==2
            load([var.ImageFolder,'/',var.ImageName,'/stress.mat'])
            sReturn.stress = data.stress;
            set(handles.disp_stress,'Enable','on')
        end
    case 'check'
        disp('Checking availability of TFM data')
        if exist([var.ImageFolder,'/',dir],'dir')==0
            sReturn = 0;
            return
        else
            %directory exists
            sReturn = 1;
            
            %load settings for gui parameter field
            if exist([var.ImageFolder,'/',dir,'/nodes.mat'],'file')==2
                load([var.ImageFolder,'/',dir,'/nodes.mat'],'data')
                set(handles.ctfm_threshold,'String',data.threshold)
                handles.var.threshold = data.threshold;
            end
            if exist([var.ImageFolder,'/',dir,'/mesh.mat'],'file')==2
                load([var.ImageFolder,'/',dir,'/mesh.mat'])
                try
                    set(handles.ctfm_set_pitch,'String',data.pitch)
                    handles.var.pitch = data.pitch;

                    entry = f_factor_mapping(handles,data.factor,'get');
                    set(handles.ctfm_set_factor,'Value',entry)
                    handles.var.factor = data.factor;
                end
                try
                    set(handles.ctfm_dist_error,'String',data.dist_error)
                    handles.var.dist_error = data.dist_error;
                    
                    set(handles.ctfm_angle_error,'String',data.angle_error)
                    handles.var.angle_error = data.angle_error;
                end
            end
            return
        end
end