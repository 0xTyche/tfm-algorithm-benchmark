%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%                                                                                   %
%                             Copyright (c) 2014-2015                               %
%				      Manuel Zündel (zuendel@imes.mavt.ethz.ch)                     %
%                       Alexander E. Ehret and Edoardo Mazza                        %
%				       Experimental Continuum Mechanics Group                       %
%				    Institute of Mechanical Systems, ETH Zürich                     %
%				                All rights reserved.                                %
%                                                                                   %
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%


function [ F,lambda ] = Fitness(triangles,xy_coords,L )
% Compute QD mesh Fitness
% Defined as the deviation from the equilateral triangular frid
    d=[];
    
    for i=1:length(triangles(:,1))
        P1=xy_coords(triangles(i,1),:);
        P2=xy_coords(triangles(i,2),:);
        P3=xy_coords(triangles(i,3),:);
        d12=norm(P1-P2);
        d23=norm(P2-P3);
        d31=norm(P3-P1);
        d(i,:)=[d12,d23,d31];   
    end
    
    F=sum(sum((d-L).^2))/(length(d)*3);
    lambda_av=mean(mean(d/L));
    lambda_min=min(min(d/L));
    lambda_max=max(max(d/L));
    lambda=[lambda_av,lambda_max,lambda_min];
end