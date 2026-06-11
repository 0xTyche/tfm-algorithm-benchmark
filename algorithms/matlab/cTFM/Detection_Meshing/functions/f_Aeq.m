%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% f_Aeq is called by the cTFM mesh generator                %
%                                                           %
% This function is called during the meshing procedure. It  %
% generates the matrix Aeq for the optimization during the  %
% process of finding the image border.                      %
%                                                           %
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

function [A,x] = f_Aeq(cluster,xcoords,ycoords,M,varargin)
    if isempty(varargin) == 0
        x_edge = varargin{1};
        y_edge = varargin{2};
        ind_edge = varargin{3}';
        ind_orig = [cluster;ind_edge];
        
        xcoords = [xcoords;x_edge];
        ycoords = [ycoords;y_edge];
    else
        ind_orig = cluster;
    end
    cluster_ind = cluster;
    ClusterTree = createns([xcoords,ycoords],'NSMethod','kdtree','Distance','euclidean');
    iNrNodes = length(cluster_ind);
    
    if iNrNodes < M
        N = iNrNodes;
    else
        N = M;
    end

    x = zeros(iNrNodes*(N-1),2);
    
    for i = 1:iNrNodes
        ind_closest = knnsearch(ClusterTree,ClusterTree.X(i,:),'k',N);
        ind_closest(1) = [];
        for j = 1:N-1
            x(N*(i-1)+j,:) = sort([ind_closest(j),i]);
        end
    end
    x = unique(x,'rows');
    x(x(:,1)==x(:,2),:) = [];
    
    A = zeros(iNrNodes,length(x));
    
    for i = 1:iNrNodes
        ind = logical(sum(ismember(x,i),2));
        A(i,ind) = 1;
    end
    
    x = ind_orig(x);
    
end