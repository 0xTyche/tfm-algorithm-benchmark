%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% f_fixed_edges is called by the cTFM mesh generator        %
%                                                           %
% This function is called during meshing.It returns the     %
% indices of the edges which are assumed to be safe.        %
%                                                           %  
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

function ind_fixed_edge = f_fixed_edges(hex_index)
    k = 1;
    ind_fixed_edge = sum(sum(find(hex_index)));
    for i=1:size(hex_index,1)
        n = find(hex_index(i,:),1,'last');
        for j = 1:n
            if i < hex_index(i,j)
                ind_fixed_edge(k,1) = i;
                ind_fixed_edge(k,2) = hex_index(i,j);
            else
                ind_fixed_edge(k,2) = i;
                ind_fixed_edge(k,1) = hex_index(i,j);
            end
            k=k+1;
        end
    end
    ind_fixed_edge = unique(ind_fixed_edge,'rows');
%     
%     hold on
%     for i = 1:length(ind_fixed_edge)
%         line([xcoords(ind_fixed_edge(i,1)),xcoords(ind_fixed_edge(i,2))],...
%            [ycoords(ind_fixed_edge(i,1)),ycoords(ind_fixed_edge(i,2))]...
%            ,'Color','w')
%     end