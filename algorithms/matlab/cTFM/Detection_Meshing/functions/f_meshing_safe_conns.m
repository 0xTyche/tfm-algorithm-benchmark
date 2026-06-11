%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% f_meshing_safe_conns is called by the cTFM mesh generator %
%                                                           %
% This function is called during the meshing procedure. It  %
% meshes the easily found mesh in regions with low          %
% deformation by simply connecting each dot to its six      %
% neighbors given that they are within the tolerance of     %
% the parameters meshing_threshold and angle_threshold.     %
%                                                           %
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

function [hex_index,hex_distance,too_many]=f_meshing_safe_conns(manual_conn,KDtree,iNrPoints,pitch,xcoords,ycoords,hex_index,dist_error,angle_error,factor)
%settings
set_grid_spacing = pitch; %[um]
meshing_threshold = dist_error/factor;%1.5; %deviation [px]
angle_threshold = angle_error;%10; %deviation of angle [°]
too_many = [];

for i = 1:iNrPoints
%     if i == 18
%         i
%     end
    iNrC = 6;
    %distinction between points with manual connections and those without
    %needs to made at this point. The nodes with manual connections need to
    %include that connection as well as fewer than 6 missing ones
%     if sum(sum(ismember(manual_conn,i)))>0
%         %manual connections for this point are available
%         iNrMC = sum(sum(ismember(manual_conn,i))); %number of manual connections
%         iNrC = 6 - iNrMC; %number of connections missing
%         %if the manual connection is within the 6 closest, then it can
%         %be proceeded as without manual connection.
%         [ind_closest,~] = knnsearch(KDtree,KDtree.X(i,:),'k',iNrC+1);
%         for j = 1:size(manual_conn,1) %for each manual connection:
%             %check if they are connected to the current point i manually:
%             mc_connected_to_pointi = sum(ismember(manual_conn(j,:),i));
%             ind_mc = manual_conn(ismember(manual_conn(j,:),i)==0);
%             if isempty(find(ismember(ind_closest,ind_mc),1)) && mc_connected_to_pointi == 1
%                 %the manual connection is not within iNrC closest
%                 [ind_closest,distance] = knnsearch(KDtree,KDtree.X(i,:),'k',iNrC+1);
%                 dist_mc = sqrt((xcoords(i)-xcoords(ind_mc))^2+(ycoords(i)-ycoords(ind_mc))^2);
%                 ind_closest = [ind_closest,ind_mc];
%                 distance = [ind_closest,dist_mc];
%             elseif isempty(find(ismember(ind_closest,ind_mc),1))==0 && mc_connected_to_pointi == 1
%                 %at least one manual connection is within the iNrC closest,
%                 %thus the next closest point needs to also be taken (manual
%                 %connection is redundant in the sense of finding closest
%                 %points)
%                 [tmp_ind_closest,tmp_distance] = knnsearch(KDtree,KDtree.X(i,:),'k',7);
%                 %find and add the closest point that is not yet connected to the pool
%                 ind_tmp = find(ismember(tmp_ind_closest,ind_closest),1,'last');
%                 ind_closest = [ind_closest,tmp_ind_closest(ind_tmp+1)];
%                 distance = [ind_closest,tmp_distance(ind_tmp+1)];
%             else
%                 %this manual connection does not effect the current point
%                 %void
%             end
%         end
%         %if, however, the manual connection is not within the 6 closest,
%         %then only iNrC points must be found. Then the checks must be
%         %conducted with the iNrC points as well as the manual connected
%         %point
%     else
%     
%         %2. find closest 7 point (the point itself is also found as closest
%         %solution
        
        [ind_closest,distance] = knnsearch(KDtree,KDtree.X(i,:),'k',iNrC+1);
%     end
    %3. Remove the point itself as closest solution. The remaining 6 are
    %the closest points
    ind_closest(1) = [];
    distance(1) = [];
    
    %4. Check the deviation of the distances between the closest points
    fit = std(distance);

    %5. if deviation is below a threshold, the mesh can be made to the
    %connecting point
    
    %check angle in hexagon
    angle_fit = 2;
    if fit < meshing_threshold %* set_grid_spacing/1.5
        [angle_fit,max_angle_delta] = f_angle_std(xcoords(i),ycoords(i),...
            xcoords(ind_closest),ycoords(ind_closest));
        
    end
    if fit < meshing_threshold && angle_fit < angle_threshold
        hex_index(i,:) = ind_closest;
        hex_distance(i,:) = distance;
        
        %6. add the connection also to the point to which the connection is
        %made, if it not yet available
        for j = 1:6
            %6.1 find connections already available
            tmp_i=hex_index(ind_closest(j),:)==i; %if the sum of this is 0, the connection needs to be added
            tmp_0=hex_index(ind_closest(j),:)==0; %if the sum of this is 0, there are already 6 connections
            if sum(tmp_i)==0 && sum(tmp_0)>0 
                K = length(find(hex_index(ind_closest(j),:))); 
                hex_index(ind_closest(j),K+1) = i; %adding point to connections
                hex_distance(ind_closest(j),K+1) = distance(j); 
            elseif sum(tmp_i)==0 && sum(tmp_0)==0
                %6.2 if six connection are already available and a seventh
                %should be added, an error in the meshing has occured. meshing
                %threshold is too generous - lower it.
                info.type = -1;
                info.discription = 'Error occured during the meshing. Lower the interdot distance threshold and run again.';
                disp('Error - Connection with 7 likely')
                %return
                too_many = [too_many;i;ind_closest(j)];
            else
                %if sum(tmp_i) == 0, that means this connections not yet
                %made to the connecting point, needs to be added
            end
        end
    end
end