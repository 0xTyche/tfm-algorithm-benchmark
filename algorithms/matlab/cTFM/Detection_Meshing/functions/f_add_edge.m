%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% f_add_edge is called by the cTFM mesh generator           %
%                                                           %
% This function lets the user manually add an edge between  %
% two nodes. These edges are used to split large unmeshed   %
% areas into smaller areas to speed up optimization. These  %
% manual edges however have no influence on the "safe"      %
% meshing.                                                  %
%                                                           %
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

function [manual_conn]=f_add_edge(var)
if isfield(var,'manual_conn')==0
    manual_conn = [];
else
    manual_conn = var.manual_conn;
end
    
[x,y] = ginput(2);


IDX = zeros(2,1);
D = zeros(2,1);
for i = 1:2
    [IDX(i),~] = knnsearch(var.KDTree.X,[x(i),y(i)]);
end

manual_conn = [manual_conn;IDX'];
hold on
line([var.xcoords(IDX(1)),var.xcoords(IDX(2))],...
   [var.ycoords(IDX(1)),var.ycoords(IDX(2))],...
    'Color',[1 0 1]);