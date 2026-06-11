%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% f_delete_node is called by the cTFM mesh generator        %
%                                                           %
% This function lets the user delete any node that was      % 
% either detected by the algorithm or added manually.       %
%                                                           %
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

function IDX = f_delete_node(KDTree)
    [x,y] = ginput(1);
    [IDX,D] = knnsearch(KDTree.X,[x,y]);
    