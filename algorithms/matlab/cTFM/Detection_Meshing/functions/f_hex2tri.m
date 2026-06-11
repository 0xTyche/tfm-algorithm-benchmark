%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% f_hex2tri is called by the cTFM mesh generator            %
%                                                           %
% This function extracts the triangles from the triangular  %
% grid in hex_index.                                        %
%                                                           %
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

function triangles = f_hex2tri(hex_index)
% this function extracts the triangles from the hexagonal grid
iNrPoints = length(hex_index);
triangles = zeros(2*iNrPoints,3);
l = 1; %this is the running variable for new triangles
for i = 1:iNrPoints
    %only the points with six connecting points are considered
    if length(find(hex_index(i,:))) == 6
       %entering this loop means that six possible triangles are around
       %this point. Some may already be assigned a number, so must be
       %skipped
       
       
       %loop through all connecting points
       for j = 1:6
            %loop through possible 3. points in triangle
            for k = 1:6
                %point can not be the same twice
                if j ~= k
                    point1 = i;
                    point2 = hex_index(i,j);
                    point3 = hex_index(i,k);
                    %condition that the three points form a triangle of the
                    %grid and not a random one is checked below
                    if sum(ismember(hex_index(point2,:),point3)) > 0
                        %condition that these three points are not already
                        %allocated to another triangle
                        if max(sum(ismember(triangles,[point1,point2,point3])')) < 3
                            triangles(l,:) = [point1,point2,point3];
                            l = l + 1;
                        end
                    end
                end
            end
       end
   end
end
%removing not used but preallocated lines
triangles(sum(triangles')==0,:)=[];
