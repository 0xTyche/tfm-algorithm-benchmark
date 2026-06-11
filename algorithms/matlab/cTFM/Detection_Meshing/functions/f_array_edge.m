%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% f_array_edge is called by the cTFM mesh generator         %
%                                                           %
% This function takes coordinates of all nodes              %
% (xcoords,ycoords) as well as the indices of the nodes     %
% which are located on the border of the image. It then     %
% finds the shortes path to connect all of them to create   %
% the "image border". Currently this function has no effect %
% on the subsequent meshing steps.                          %
%                                                           %
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

function array_edge = f_array_edge(xcoords,ycoords,ind_edge,ind_fixed_edge)
    [Aeq,edge_map] = f_Aeq(ind_edge,xcoords(ind_edge),ycoords(ind_edge),5);
    ind_orig_ArrayEdges = edge_map; %edge map in original (full) indices

    %remove edges that cross existing edges from certain boundaries
    XY1 = [xcoords(ind_orig_ArrayEdges(:,1)),ycoords(ind_orig_ArrayEdges(:,1)),...
        xcoords(ind_orig_ArrayEdges(:,2)),ycoords(ind_orig_ArrayEdges(:,2))]; %all possible edges around image border
    XY2 = [xcoords(ind_fixed_edge(:,1)),ycoords(ind_fixed_edge(:,1)),...
        xcoords(ind_fixed_edge(:,2)),ycoords(ind_fixed_edge(:,2))]; %all edges already existing
    intersect = lineSegmentIntersect(XY1,XY2);

    %remove crossing edges from pool of possibilities in 'ind_orig_edges'
    [Aeq,ind_orig_ArrayEdges] = f_remove_x(ind_orig_ArrayEdges,intersect,Aeq,'edge');

    
    %create constraints for edges, such that crossing is not possible 
    XY = [xcoords(ind_orig_ArrayEdges(:,1)),ycoords(ind_orig_ArrayEdges(:,1)),...
        xcoords(ind_orig_ArrayEdges(:,2)),ycoords(ind_orig_ArrayEdges(:,2))]; %only feasible edges taken into account
    intersect = lineSegmentIntersect(XY,XY);
    [Aloeq] = f_Aloeq(intersect);
    
    %solve integer linear problem
    f = ones(size(Aeq,2),1);%ones(length(Aeq),1);
    intcon = 1:size(Aeq,2);%length(Aeq);
    beq = 2*ones(length(ind_edge),1);


    vertex_length = f_vertex_length(xcoords,ycoords,ind_orig_ArrayEdges);

    result = f_gurobi(Aloeq,Aeq,beq,vertex_length);
    x = result.x;
    
    array_edge = ind_orig_ArrayEdges(logical(x),:);

         
    hold on
    for i = 1:length(ind_orig_ArrayEdges)
        if x(i) == 1 
        line([xcoords(ind_orig_ArrayEdges(i,1)),xcoords(ind_orig_ArrayEdges(i,2))],...
           [ycoords(ind_orig_ArrayEdges(i,1)),ycoords(ind_orig_ArrayEdges(i,2))]...
           ,'Color','y')
        end
    end
