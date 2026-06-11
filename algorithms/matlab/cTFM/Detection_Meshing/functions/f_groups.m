%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% f_groups is called by the cTFM mesh generator             %
%                                                           %
% This function takes all the available edges and groups    %
% them. It distinguishes between connection around an un-   %
% meshed cluster, edges protruding into an unmeshed         %
% cluster and manual connections amongst others. These      %
% distinctions are used later on.                           %
%                                                           %
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

function groups = f_groups(ind_missing_conn,hex_index,ind_fixed_edge,array_edge,ind_edge,manual_conn)
    if isempty(ind_missing_conn)
        groups.boundary_nodes = [];
        groups.boundary_conns = [];
        groups.inward_conns = [];
        groups.array_edge = [];
        groups.ind_cluster2edge = [];
        groups.manual_conn = manual_conn;
        return
    end
    tmp_boundary_nodes = ismember(hex_index,ind_missing_conn);
    k=0;
    %find all the nodes surrounding the nodes without 6 connections
    for i = 1:size(tmp_boundary_nodes,1)
        for j = 1:6
            if tmp_boundary_nodes(i,j) == 1 %this node has a connection to at least one node, that is not fully connected
                if ismember(i,ind_missing_conn)==0 %the found node has 6 connection
                    %node must be saved as boundary node
                    k = k+1;    
                    boundary_node(k) = i;
                    inward_conn(k,1) = i;
                    inward_conn(k,2) = hex_index(i,j);
                end
            end
        end
    end
    boundary_node=unique(boundary_node);
    %find connections of boundary nodes already existing in the hexagonal
    %grid (hex_index)
    k = 0;
    for i = 1:length(boundary_node)
        tmp_ind = ismember(hex_index(boundary_node(i),:),boundary_node); %tmp_ind shows which entries are also boundary nodes
        ind_boundary_conn = find(tmp_ind); %index for boundary nodes connected to current node(i)
        for j = 1:length(ind_boundary_conn)
           k = k+1;
           if boundary_node(i) < hex_index(boundary_node(i),ind_boundary_conn(j))
               boundary_conn(k,1) = boundary_node(i);
               boundary_conn(k,2) = hex_index(boundary_node(i),ind_boundary_conn(j));
           else
               boundary_conn(k,2) = boundary_node(i);
               boundary_conn(k,1) = hex_index(boundary_node(i),ind_boundary_conn(j));
           end
        end
    end
    %manual connections are no also considered borders
    boundary_conn = [boundary_conn;manual_conn];
    
    boundary_conn = unique(boundary_conn,'rows');
    
    %find connections between array edge and cluster edge
    tmp1 = find(sum(ismember(ind_fixed_edge,ind_edge),2)==1);
    tmp2 = find(sum(ismember(ind_fixed_edge,boundary_node),2)==1);
    a = ismember(tmp1,tmp2);
    
    %create vector with lines going from cluster edges to array edges.
    %However, the manual connections must be excluded
    ind_cluster2edge = ind_fixed_edge(tmp1(a),:);
    tmp2 = find(sum(ismember(ind_cluster2edge,manual_conn),2)==2); %index of cluster2edge connections that are also manual connections
    ind_cluster2edge(tmp2,:)=[]; %deleting these manual connections
    
    groups.boundary_nodes = boundary_node;
    groups.boundary_conns = boundary_conn;
    groups.inward_conns = inward_conn;
    groups.ind_fixed_conns = ind_fixed_edge;
    groups.array_edge = array_edge;
    groups.ind_cluster2edge = ind_cluster2edge;
    groups.manual_conn = manual_conn;
%     hold on
%     for i = 1:length(boundary_conn)
%         line([xcoords(boundary_conn(i,1)),xcoords(boundary_conn(i,2))],...
%            [ycoords(boundary_conn(i,1)),ycoords(boundary_conn(i,2))]...
%            ,'Color','r')
%     end
%     for i = 1:length(manual_conn)
%         line([xcoords(manual_conn(i,1)),xcoords(manual_conn(i,2))],...
%            [ycoords(manual_conn(i,1)),ycoords(manual_conn(i,2))]...
%            ,'Color','m')
%     end