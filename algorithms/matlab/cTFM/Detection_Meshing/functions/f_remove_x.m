%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% f_remove_x is called by the cTFM mesh generator           %
%                                                           %
% This function is called during the meshing procedure. It  %
% removes impossible edges from Aeq because the intersect   %
% with fixed edges    										%
%                                                           %
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

function [Aeq,ind_orig_edges] = f_remove_x(ind_orig_edges,intersect,Aeq,sCase)
    A = intersect.intAdjacencyMatrix;
    Delta = intersect.intNormalizedDistance1To2;
    
    ind_manual = [];
    
    if strcmp(sCase,'edge')
        ind_manual = [];
    elseif strcmp(sCase,'cluster')
        [ind_manual,tmp]=find(intersect.coincAdjacencyMatrix);
    end
    
    [N,M] = size(A); %N == number of node possibilities, M == number of existing nodes
    ind_remove = [];
    k = 1;
    for i=1:N %for every possible edge...
        for j=1:M %... the intersection with existing edges is checked.
            if A(i,j) == 1 && Delta(i,j) > 0.0001 && Delta(i,j) < 0.9999
%                 if i == 28
%                     disp(['i: ' i ';  j: ' j]);
%                 end
                %intersection occuring between possible edge i and certain edge j
                %if the is reached, then edge i crosses an existing edge
                %and must be removed. Hence, i is saved for later.
                ind_remove(k) = i;
                k = k+1;
            end
        end
    end
    if isempty(ind_manual)==0
        ind_remove = unique([ind_remove,ind_manual']);
    else
        ind_remove = unique(ind_remove);
    end
    
    if isempty(ind_remove)==0
        ind_orig_edges(ind_remove,:) = [];
        Aeq(:,ind_remove) = [];
    end
    Aeq = sparse(Aeq);