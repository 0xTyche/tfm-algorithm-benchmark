%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% f_angle_std is called by the cTFM mesh generator           %
%                                                           %
% This function takes coordinates of a point (x0,y0) and    %
% its six neighbors (xcoords,ycoords). It then calculates   %
% all the angles between the edges and returns their        %
% standard error as well as the largest off-set from a 60°  %
% angle.                                                    %
%                                                           %
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

function [angle_fit,max_delta] = f_angle_std(x0,y0,xcoords,ycoords)
angles = zeros(6,1);
theta = zeros(6,1);
for i = 1:6
        a = [xcoords(i)-x0,ycoords(i)-y0];
        b = [xcoords-x0,ycoords-y0];
%         if length(b)<6
%             b
%         end
        for j = 1:6
            dotp = a(1)*b(j,1) + a(2)*b(j,2);
            det = a(1)*b(j,2) - a(2)*b(j,1);
            theta(j) = atan2(det, dotp)/pi*180 ;
        end
        %find smallest positive angle
        theta(theta <= 0) = 180;
        [~,ind] = min(theta-60);
        angles(i) = theta(ind);
end
angle_fit = std(angles);
max_delta = max(abs(angles-60));
%to do: improve, such that not every single angle needs to be
    %calculated
