%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% f_disp_control is called by the cTFM mesh generator       %
%                                                           %
% This function sets the environment variables for the axes %
% display function to read, which then displays the         %
% according plots.                                          %
%                                                           %
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

function f_disp_control(handles,sCase,enable,value)
switch sCase
    case 'img'
        set(handles.ctfm_disp_image, 'enable', enable)
        set(handles.ctfm_disp_image, 'value', value)
    case 'nodes'
        set(handles.ctfm_disp_nodes, 'enable', enable)
        set(handles.ctfm_disp_nodes, 'value', value)
    case 'nodes3D'
        set(handles.ctfm_disp_nodes3D, 'enable', enable)
        set(handles.ctfm_disp_nodes3D, 'value', value)
    case 'mesh'
        set(handles.ctfm_disp_mesh, 'enable', enable)
        set(handles.ctfm_disp_mesh, 'value', value) 
    case 'all'
        f_disp_control(handles,'img',enable,value)
        f_disp_control(handles,'nodes',enable,value)
        f_disp_control(handles,'nodes3D',enable,value)
        f_disp_control(handles,'mesh',enable,value)
end
if value == 1
    set(handles.ctfm_disp_apply,'enable','on')
end