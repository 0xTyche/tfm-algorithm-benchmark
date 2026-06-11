%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% f_add_node is called by the cTFM mesh generator           %
%                                                           %
% This function lets the user manually add a node to the    %
% image. This is useful if the detecion algorithm fails     %
% to detect a node.                                         %
%                                                           %
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

function [x,y] = f_add_node(var)
    img = var.img;
    
    [x_click,y_click] = ginput(1);
    
    x = x_click;
    y = y_click;
    
    
