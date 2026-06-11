%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% f_clusters is called by the cTFM mesh generator           %
%                                                           %
% This function's task is to find and sort the edges around %
% the unmeshed clusters. It does this in multiple steps.    %
% Firstly it removes all the unnecessary cluster edges, i.e.%
% the ones contain as single edges in a cluster and the     %
% single edges looking into the cluster. Once the cluster   %
% edges are "clean" they are sorted. This is done by        %
% walking around the clusters. The sorted cluster edges as  %
% well as the orientation of sorting (cw, ccw).             %
%                                                           %
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

function clusters = f_clusters(groups,ind_missing_conn,xcoords,ycoords,hex_index)
% A_tmp = groups.boundary_conns;
% A_tmp = A_tmp' + A_tmp;
% A_sparse = sparse(A_tmp(:,1),A_tmp(:,2),1);
% [C,G]=graphconncomp(A_sparse);
if isempty(ind_missing_conn)
    clusters.N = 0;
    return
end

if isfield(groups,'manual_conn')==0
    groups.manual_conn = [];
end

%concatenate array_edge, cluster_boundary_conns and intermediate
%connections to possible cluster edge vertices
cluster_edges = [groups.boundary_conns;groups.array_edge;....
    groups.ind_cluster2edge];

%find single branches of groups.boundary_conns to exclude them from being
%used as boundary
bin_range=[min(min(cluster_edges)),max(max(cluster_edges))];

bincounts = histcounts(cluster_edges(:), (bin_range(1)-0.5):(bin_range(2)+0.5))';
tmp_ind=find(ismember(bincounts,1));
single_conn_ind = bin_range(1)+tmp_ind-1; %index of nodes that are at the end of branches that are not closed
single_conns=find(ismember(cluster_edges,single_conn_ind));
single_conns = mod(single_conns,length(cluster_edges));  %index of edges that are not in closed loops
single_conns = unique(single_conns);
removed_edges = single_conns; %this vector keeps count of removed vertices at each node

%every branch that is not in a closed loop needs to be removed completely.
%Every branch is walked along to remove the entire branch
add_conns = [];

for i = 1:length(single_conns)
    current_edge = single_conns(i);
    current_node_ind = find(ismember(single_conn_ind,cluster_edges(current_edge,:)));
    current_node = single_conn_ind(current_node_ind(1));
    if single_conns(i) == 11
        i;
    end
    while true
        current_edge;
%         if current_node == 59
%             i
%             hold on
%             scatter(xcoords(current_node),ycoords(current_node),200,'pr')
%         end
        %single points that are fully connected, but don't have any edges
        %must be ignored while looking for cluster boundaries:
        if isempty(current_edge)
            break;
        end
        if size(current_edge,1)>1
            break;
        end
        if current_edge > size(groups.boundary_conns,1)
            break;
        end
        edge_tmp = groups.boundary_conns(current_edge,:); %edge with single connection
        current_node = edge_tmp(edge_tmp ~= current_node);
        tmp = ismember(cluster_edges,current_node);
        tmp = sum(tmp,2);
     
        %find if a branch connecting to this node has already been removed.
        %If so this is one less connections to this node. Imagine a polygon 
        %with this structure: _Y_ . The entire Y needs to be
        %ignored/removed
        
        removed_nodes = cluster_edges(removed_edges,:);
        removed_nodes = removed_nodes(:); %all nodes that have had an edge removed, can be greater than one
        
        total_conn = sum(tmp)-sum(removed_nodes==current_node); %total connections to node not yet removed
         
        
        nr_edge = sum(tmp);
        %nr_nodes = sum(sum(ismember(groups.boundary_conns,current_node)));
        nr_nodes = sum(sum(ismember(cluster_edges,current_node))); %total connections to node
        if total_conn > 1 %&& nr_nodes > 2%the next vertex has 3 or more connections, thus the branch end
            break;
        elseif nr_nodes == 1 %freestanding branch in the middle of a cluster
            break;
        else
            current_edge = find(tmp == 1);
            %if more than one edge is available, then the one that hasn't
            %been added needs to be taken:
            if size(current_edge,1)>1
                current_edge = current_edge(ismember(current_edge,[single_conns;add_conns])==0);
            end
            if sum(ismember(add_conns,current_edge))>0
                break;
            elseif sum(ismember(single_conn_ind,current_node))>0 %end of free standing branch has been
                break;
            end
            removed_edges = unique([removed_edges;current_edge]);
            add_conns = [add_conns;current_edge];
        end
    end
end
single_conns = [single_conns;add_conns];

k=1;
% for i=1:C
%    tmp = ismember(G,i);
%    if sum(tmp) > 1
%        clusters.ind{k,1}=i;
%        clusters.edges{k,:}= find(tmp);
%        k = k+1;
%    end
% end
% iNrClusters = k-1;
% hold on

%temporary twerk
% backup = groups.boundary_conns;
 groups.boundary_conns = cluster_edges;


%sort the cluster edges to get polygon
logical_inpoly = zeros(length(ind_missing_conn),1); %0: not yet in a polygon, 1: in a polygon
while true
    [logical_point,ind_point] = ismember(0,logical_inpoly);
    if logical_point == 1 %Points not in a polygon still exist
        ordered_vertices = [];
        edge_used = zeros(length(groups.boundary_conns),1);
        
        
        %add single edges as used, such that they are excluded from being
        %used as cluster boundary
        edge_used(single_conns) = 1;
        edge_used_new = edge_used;
        %select first point that is not in a polygon. from here create a
        %line in negative x direction and find its intersection with the
        %cluster edge
        xc = xcoords(ind_missing_conn(ind_point));
        yc = ycoords(ind_missing_conn(ind_point));
        linec = [xc,yc,0,yc];
        xb1 = xcoords(groups.boundary_conns(:,1));
        yb1 = ycoords(groups.boundary_conns(:,1));
        xb2 = xcoords(groups.boundary_conns(:,2));
        yb2 = ycoords(groups.boundary_conns(:,2));
        boundarylines = [xb1,yb1,xb2,yb2];
        %check intersection
        intersect = lineSegmentIntersect(linec,boundarylines);
%         [~,ind_tmp]=sort(intersect.intNormalizedDistance2To1(intersect.intAdjacencyMatrix));
        edge_b = find(intersect.intAdjacencyMatrix);
        
        %find the shortest mean distance of the point xc/yc to the center
        %of the possible lines it crosses
        xm = 1/2 * (xcoords(groups.boundary_conns(edge_b,1)) + xcoords(groups.boundary_conns(edge_b,2)));
        ym = 1/2 * (ycoords(groups.boundary_conns(edge_b,1)) + ycoords(groups.boundary_conns(edge_b,2)));
        [~,ind_tmp]=sort((xm-xc).^2+(ym-yc).^2);
        %starting vertex for the walk along the inside of the boundary
        ordered_vertices(1) = groups.boundary_conns(edge_b(ind_tmp(1)),1);
        ordered_vertices(2) = groups.boundary_conns(edge_b(ind_tmp(1)),2);
        
%         if ordered_vertices(1) == 97
%             odered_vertices
%         end
        
        %saving edge as used
        ind_edge = sum(ismember(groups.boundary_conns,[ordered_vertices(1),ordered_vertices(2)]),2);
        [~,ind_tmp] = ismember(ind_edge,2);
        edge_used(logical(ind_tmp)) = 1;
        %angle of first edge. This angle direction must be kept the same
        %while walking on the border
        initial_angle = atan2(ycoords(ordered_vertices(2)) - ycoords(ordered_vertices(1)),...
            xcoords(ordered_vertices(2)) - xcoords(ordered_vertices(1)));
        if initial_angle >= 0;
            factor = 1;
        else
            factor = -1;
        end
        i = 2;
        while true
            tmp_ind = find(sum(ismember(groups.boundary_conns,ordered_vertices(i)),2)); %find row containing entry with last entry in 'ordered vertices'
            
            
            %first remove all the single_conns from pool of possible edges
            %(they have been distinguished earlier)
            single_ind = ismember(tmp_ind,single_conns);
            tmp_ind(single_ind)=[];
            
            %maybe this is unneccesary, and should not be check:
            %tmp_ind2 = find(edge_used(tmp_ind)==0);
            tmp_ind2 = 1:length(tmp_ind); %small workaround to not have to change code below
            
            %sometimes an edge must be used twice. Walking it both ways is
            %possible. if this happens, then tmp_ind2 is empty. Now all the
            %edges that were used are viable again if there are none that
            %have not been used attach to this vertex
            
%             k
%             i
%             
%             if k == 12% && i == 2
%                 k
%             end
         
            if size(tmp_ind2,2) == 1 %dead end... only way is back the same connection
                tmp_ind2 = find(edge_used_new(tmp_ind)==0);
                
                current_edge = groups.boundary_conns(tmp_ind(tmp_ind2),:);
                %remove edge that was just walked along
                ind_last_edge = find(sum(ismember(current_edge,ordered_vertices(end-1:end)),2)==2);
                current_edge(ind_last_edge,:)=[];
                
            elseif size(tmp_ind2,2) == 2 %this should be normal case, one incoming and one outgoing edge
                %First remove the incoming edge from pool edge 
                incoming = [ordered_vertices(end-1),ordered_vertices(end)];
                current_edge = groups.boundary_conns(tmp_ind(tmp_ind2),:);
                incoming_ind = find(sum(ismember(current_edge,incoming),2)==2);

                current_edge(incoming_ind,:) = [];
                
                %maybe both are already used...
                
            elseif size(tmp_ind2,2)>2
                    %if this is reached it means there is more than on possible
                    %way to continue. First remove the incoming edge from pool edge 
                    incoming = [ordered_vertices(end-1),ordered_vertices(end)];
                    current_edge = groups.boundary_conns(tmp_ind(tmp_ind2),:);
                    incoming_ind = find(sum(ismember(current_edge,incoming),2)==2);
                    
                    current_edge(incoming_ind,:) = [];
                    
                    %Now the angle criterium must be used
                    angle_edge = zeros(size(current_edge,1),1);
                    angle = zeros(size(current_edge,1),1);
                    tmp_ind = ismember(current_edge,ordered_vertices(i));
                    v1 = [xcoords(ordered_vertices(i-1))-xcoords(ordered_vertices(i));...
                        ycoords(ordered_vertices(i-1))-ycoords(ordered_vertices(i))];
                    for j=1:size(current_edge,1)
                        tmp_edge = current_edge(j,:);
                        angle_edge(j) = tmp_edge(tmp_ind(j,:)==0);
                        v2 = [xcoords(angle_edge(j))-xcoords(ordered_vertices(i));...
                            ycoords(angle_edge(j))-ycoords(ordered_vertices(i))];
                       angle(j) = atan2(v1(1)*v2(2)-v1(2)*v2(1), dot(v2,v1));                   
                    end
                    angle(angle<0) = angle(angle<0)+2*pi;
                    if factor == 1
                        [~,tmp_ind] = min(angle);
                    else    
                        [~,tmp_ind] = max(angle);
                    end
                    current_edge = current_edge(tmp_ind,:);
            end
            %find vertex of edge different from the one it just came from
            tmp_ind3 = ismember(current_edge,ordered_vertices(i));
            i = i + 1;
            
            ordered_vertices(i) = current_edge(tmp_ind3==0);
            %if circle is closed then the polygon is closed
            if ordered_vertices(i) == ordered_vertices(1)
                ordered_vertices(end) = [];
                break;
            end
            %saving edge as used
            ind_edge = sum(ismember(groups.boundary_conns,[ordered_vertices(i-1),ordered_vertices(i)]),2);
            [~,ind_tmp] = ismember(ind_edge,2);
            edge_used(logical(ind_tmp)) = 1;
        end
        
        %get rid of inlets into cluster
        if length(ordered_vertices) ~= length(unique(ordered_vertices))
            l = 1;
            while true 
                if sum(ordered_vertices == ordered_vertices(l)) > 1 %vertex with multiple
                    assert(sum(ordered_vertices == ordered_vertices(l))==2)
                    tmp_ind = find(ordered_vertices == ordered_vertices(l));
                    ordered_vertices(tmp_ind(1)+1:tmp_ind(2))=[];
                end
                l = l+1;
                if l > length(ordered_vertices)
                    break
                end
            end
        end
        
        %save order of vertices
        clusters.edges{k,:}= ordered_vertices;
        
        %save all vertices in the polygon
        [inpoly,onpoly] = inpolygon(xcoords,ycoords,xcoords(ordered_vertices),ycoords(ordered_vertices));
        inpoly = find(inpoly);
        onpoly = find(onpoly);
        ind_cluster = ismember(inpoly,onpoly);
        
        clusters.incluster{k,:} = inpoly(~ind_cluster);
        
%         hold on
%         scatter(xcoords(clusters.edges{k,:}),ycoords(clusters.edges{k,:}),'m')
%         scatter(xcoords(clusters.incluster{k,:}),ycoords(clusters.incluster{k,:}),'w')
        
        %save all vertices in polygon
        [ind_all_incluster,on_temp] = inpolygon(xcoords,ycoords,...
            xcoords(ordered_vertices),ycoords(ordered_vertices));
        ind_all_incluster(ind_all_incluster==on_temp) = 0;
        clusters.all_incluster{k,:} = find(ind_all_incluster);
        
        ind_cluster2 = find(inpolygon(xcoords(ind_missing_conn),ycoords(ind_missing_conn),...
            xcoords(ordered_vertices),ycoords(ordered_vertices)));
        
        logical_inpoly(ind_cluster2) = 1;
        %patch(xcoords(ordered_vertices),ycoords(ordered_vertices),'w');
        clusters.N = k;
        clusters.direction(k,1) = factor;
        
        %this cell saves the nodes which are on the array edge, but also
        %make up the cluster border. Hence, they might need connections
        clusters.array_cluster_edges{k,:} = ordered_vertices(find(ismember(ordered_vertices,groups.array_edge)));
        k = k+1;
%         if k == 23
%             k
%         end
%         

% 		drawnow;
    else
        return;
    end  
end
% for i=1:k-1
%     cluster_edges = cell2mat(clusters.edges(i,:));
%     %sort the cluster edges to get polygon
%     x = xcoords(cluster_edges);
%     y = ycoords(cluster_edges);
%     if length(cluster_edges) > 3
%         %find centroid
%         cx = mean(x);
%         cy = mean(y);
%         %find angle
%         a = atan2(y - cy, x - cx);
%         %sort and reorder according to angle
%         [~, order] = sort(a);
%         x = x(order);
%         y = y(order);
%     end    
% 
% end