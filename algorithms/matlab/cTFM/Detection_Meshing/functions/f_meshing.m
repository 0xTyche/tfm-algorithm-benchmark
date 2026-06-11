%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% f_meshing is called by the cTFM mesh generator            %
%                                                           %
% This is the main function for the mesh generation. First  %
% it f_meshing_safe_conns to find the areas of low          %
% distortion where it can generate the mesh easily. Then    %
% it groups the available edges in f_groups and sorts the   %
% borders of the unmeshed regions in f_clusters. Finally    %
% in f_meshing_optimization_laplacian the optmization is    %
% is run to find the mesh in strongly deformed regions.     %
%                                                           %
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

function [hex_index,hex_distance,groups,clusters,info_output,safe_triangles]=f_meshing(var)
%% This function meshes the grid and returns the coordinates and connections
% it may only be called via the TFM_lab gui

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%add paths of used functions that were not writen by me:
addpath('functions\lineSegmentIntersect');
addpath('functions\cpp');
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

img = var.img;
xcoords = var.xcoords;
ycoords = var.ycoords;
factor = var.factor;
KDtree = var.KDTree;
dist_error = var.dist_error;
angle_error = var.angle_error;

if isfield(var,'manual_conn')==0
    manual_conn = [];
else
    manual_conn = var.manual_conn;
end

info_output.description = [];
info_output.type = 0;
groups = [];
hex_index = [];
clusters = [];

%settings
set_grid_spacing = var.pitch; %[um]
border_range = 20; %range in which a points is considered on the edge
meshing_threshold = 1.5; %deviation [px]
angle_threshold = 10; %deviation of angle [°]

[max_y,max_x] = size(img);  
iNrPoints = length(ycoords);

disp('Start with meshing...')

%--------------- Start new  plot-----------
% figure
hold off
imshow(img,[])
hold on
scatter(xcoords,ycoords)
%------------------------------------------


%% Do circle fit around points
% this matrix later saves the index of the point surrounding the point with index
% of the row number 
% hex_index: row1: [2,3,4,5,6,7] means that point 1 has point 2 - 7 as 
% nearest points. hex_distance saves the distance to point indexed
hex_index = zeros(iNrPoints,6);
hex_distance = hex_index;

% check whether there are manual connections. Should there be, then these
% need to be included in hex_index
disp('... adding manual connections')
if isempty(manual_conn) == 0
    for i=1:size(manual_conn,1)
        n = find(hex_index(manual_conn(i,1),:),1,'last');
        if isempty(n)
            n = 0;
        end
        hex_index(manual_conn(i,1),n+1) = manual_conn(i,2);
        
        n = find(hex_index(manual_conn(i,2),:),1,'last');
        if isempty(n)
            n = 0;
        end        
        hex_index(manual_conn(i,2),n+1) = manual_conn(i,1);
    end
end

% %temp for debugging
var.already_meshed = [];

%make all the safe connections
disp('... meshing safe connections')
if isfield(var,'already_meshed')==0
    [hex_index,hex_distance,~]=f_meshing_safe_conns(manual_conn,KDtree,iNrPoints,var.pitch,xcoords,ycoords,hex_index,dist_error,angle_error,factor);
else
    hex_index = var.hex_index;
end

%extract triangles from trimesh. Makes plotting more efficient
safe_triangles = f_hex2tri(hex_index);

ind_fixed_edge = f_fixed_edges(hex_index);
%--------- Plot of safe connections-----------
trimesh(safe_triangles,xcoords,ycoords,'Color','b')
%---------------------------------------------

%7. Find the dots that do and that do not yet have 6 connections
nr_of_entries = sum(hex_index'~=0)';
missing_entries = 6 - nr_of_entries;
ind_nonfull = find(nr_of_entries ~= 6);
ind_full = find(nr_of_entries == 6);

%8. Find the points on the edge. At this point the points have 6
%connections. If not then either they point is on the edge of the image, or
%the connection was not found due to deformation. Points on the edge are
%determined first as from here on, only the inner connections 
%should be used
max_dim = max(max_x,max_y);
ind_edge_l = ones(max_dim,1);
ind_edge_r = ones(max_dim,1);
ind_edge_t = ones(max_dim,1);
ind_edge_b = ones(max_dim,1);
for i = 1:max(max_x,max_y)
    %top edge:
    ind_edge_t(i) = knnsearch(KDtree,[i,0],'k',1);
    %bottom edge:
    ind_edge_b(i) = knnsearch(KDtree,[i,max_y+1],'k',1);
    %left edge:
    ind_edge_l(i) = knnsearch(KDtree,[0,i],'k',1);
    %right edge:
    ind_edge_r(i) = knnsearch(KDtree,[max_x+1,i],'k',1);
end

ind_edge = unique([ind_edge_l;ind_edge_r;ind_edge_t;ind_edge_b]);

%ignore the ones that are considered on the edge but nevertheless 
%have 6 connection (not likely). Then find all the points in the center
ind_edge(ismember(ind_edge,ind_full))=[];
ind_missing_conn = ind_nonfull;
ind_missing_conn(ismember(ind_missing_conn,ind_edge))=[];

%connect edges such that the border of the image is defined
disp('... finding array edge')
array_edge = f_array_edge(xcoords,ycoords,ind_edge,ind_fixed_edge);

disp('... allocating edges to groups')
groups = f_groups(ind_missing_conn,hex_index,ind_fixed_edge,array_edge,ind_edge,manual_conn);

%%TODO: remove inward conns from hex_index -> they are not safe


%-------- Plot of boundaries------------------
hold on
for i = 1:length(groups.boundary_conns)
line([xcoords(groups.boundary_conns(i,1)),xcoords(groups.boundary_conns(i,2))],...
   [ycoords(groups.boundary_conns(i,1)),ycoords(groups.boundary_conns(i,2))]...
   ,'Color','r')
end
% for i = 1:length(groups.inward_conns)
% line([xcoords(groups.inward_conns(i,1)),xcoords(groups.inward_conns(i,2))],...
%    [ycoords(groups.inward_conns(i,1)),ycoords(groups.inward_conns(i,2))]...
%    ,'Color','g')
% end
for i = 1:length(groups.array_edge)
line([xcoords(groups.array_edge(i,1)),xcoords(groups.array_edge(i,2))],...
   [ycoords(groups.array_edge(i,1)),ycoords(groups.array_edge(i,2))]...
   ,'Color','y')
end
for i = 1:length(groups.ind_cluster2edge)
line([xcoords(groups.ind_cluster2edge(i,1)),xcoords(groups.ind_cluster2edge(i,2))],...
   [ycoords(groups.ind_cluster2edge(i,1)),ycoords(groups.ind_cluster2edge(i,2))]...
   ,'Color','c')
end

hold off
%---------------------------------------------

%TODO: chech which manual connection belongs to which cluster
disp('... sorting cluster boundaries')
clusters = f_clusters(groups,ind_missing_conn,xcoords,ycoords);

%% Optimization
disp('... optimizing deformed mesh')
for i = 1:clusters.N
    tic
    [edges,info_output,valid]=f_meshing_optimization_laplacian(i,info_output,groups,clusters,missing_entries,xcoords,ycoords,hex_index);
    if valid == 0
%         [edges,info_output]=f_meshing_optimization_intersection(i,info_output,groups,clusters,missing_entries,xcoords,ycoords);
    
    %End of optimization
    else % new optimization was successful, remove any existing connections in the cluster and use only the new ones
        hex_index(clusters.incluster{i,:},:) = 0;
        [irows,icols]=find(ismember(hex_index,clusters.incluster{i,:}));
        for l = 1:length(irows)
            if irows(l) == 727
                irows
            end    
            hex_index(irows(l),icols(l)) = 0;
        end
        hex_index = sort(hex_index,2,'descend');
    end
    
    toc
    hold on
        
    if size(edges,2) > 1
        for j = 1:size(edges,1)
            %check whether edge already exists, if so -> skip
            if edges(j,1)>0 && edges(j,2)>0
                if sum(hex_index(edges(j,1),:)==edges(j,2)) == 0
                
                n = find(hex_index(edges(j,1),:),1,'last');
                if isempty(n)
                    n = 0;
                end
                hex_index(edges(j,1),n+1) = edges(j,2); 
                n = find(hex_index(edges(j,2),:),1,'last');
                if isempty(n)
                    n = 0;
                end        
                
                hex_index(edges(j,2),n+1) = edges(j,1); 

        %         line([xcoords(edges(j,1));xcoords(edges(j,2))],...
        %             [ycoords(edges(j,1));ycoords(edges(j,2))'],'Color',cmap(i,:))

                line([xcoords(edges(j,1));xcoords(edges(j,2))],...
                    [ycoords(edges(j,1));ycoords(edges(j,2))'],'Color','w')
                end
            end
        end
    end
    hold off
end

hold on
for i = 1:size(groups.manual_conn,1)
line([xcoords(groups.manual_conn(i,1)),xcoords(groups.manual_conn(i,2))],...
   [ycoords(groups.manual_conn(i,1)),ycoords(groups.manual_conn(i,2))]...
   ,'Color','m')
end
hold off

% for i = 1:length(groups.inward_conns)
% line([xcoords(groups.inward_conns(i,1)),xcoords(groups.inward_conns(i,2))],...
%    [ycoords(groups.inward_conns(i,1)),ycoords(groups.inward_conns(i,2))]...
%    ,'Color','g')
% end
% %debugging figure
hold on

if info_output.type == 0
    if clusters.N == 0
        info_output.description = ['Mesh found. No optimization needed']; 
    else
        info_output.description = ['Optimal solution found for ', num2str(clusters.N),' cluster(s)']; 
    end
end 
disp('... meshing complete.')
%scatter(KDtree.X(i,1),KDtree.X(i,2),'xg');
%scatter(KDtree.X(ind_closest,1),KDtree.X(ind_closest,2),'r');
%scatter(KDtree.X(ind_nonfull,1),KDtree.X(ind_nonfull,2),'rx');
%scatter(KDtree.X(ind_missing_conn,1),KDtree.X(ind_missing_conn,2),'r');
%scatter(KDtree.X(ind_edge,1),KDtree.X(ind_edge,2),'g');
% cmap = jet(clusters.N);
% for i = 1:clusters.N
%     temp_ind = cell2mat(clusters.incluster(i));
%     scatter(KDtree.X(temp_ind,1),KDtree.X(temp_ind,2),...
%         150,'p','MarkerFaceColor',cmap(i,:));
% end
% 
% hold on
% for i = 1:iNrPoints
%     tmp = hex_index(i,:);
%     tmp(tmp ~= 0) = 1;
%     N = sum(tmp);
%     
%     line([xcoords(i)*ones(N,1)';xcoords(hex_index(i,1:N))'],...
%         [ycoords(i)*ones(N,1)';ycoords(hex_index(i,1:N))'],'Color','b')
% end

% for i = 1:length(ind_orig_edges)
% line([xcoords(ind_orig_edges(i,1)),xcoords(ind_orig_edges(i,2))],...
%    [ycoords(ind_orig_edges(i,1)),ycoords(ind_orig_edges(i,2))]...
%    ,'Color','w')
% end
% XY = XY3;
% for i = 1:length(XY)
% line([XY(i,1),XY(i,3)],[XY(i,2),XY(i,4)]...
%    ,'Color','w')
% end
% scatter(xcoords(groups.boundary_nodes),ycoords(groups.boundary_nodes),'r')
% hold off
% 
% save([path,'\',file,'_data.mat'],'xcoords','ycoords','hex_index',...
%     'hex_distance','intensity_factor','factor');
