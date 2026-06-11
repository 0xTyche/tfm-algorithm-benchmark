%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% f_vertex_length is called by the cTFM mesh generator      %
%                                                           %
% This function is called during the meshing procedure. It  %
% takes the coordinates and the indices of edges and returns%
% the length of each edge.                                  %
%                                                           %
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

function vertex_length = f_vertex_length(xcoords,ycoords,ind_orig_edges)
    vertex_length = sqrt((xcoords(ind_orig_edges(:,1)) - xcoords(ind_orig_edges(:,2))).^2 ...
        + (ycoords(ind_orig_edges(:,1)) - ycoords(ind_orig_edges(:,2))).^2);
