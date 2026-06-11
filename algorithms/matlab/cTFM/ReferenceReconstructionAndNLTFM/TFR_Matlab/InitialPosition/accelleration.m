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


function [ axy ] = accelleration( xycoords,connectivity,lock,xy,v,k,d,m ,L0)
   % Return the accelleration of a point
   
   % Initialize Force Vector
   Fxy=zeros(size(xycoords));
   
   % Set velocity of locked points to 0
   v=v.*(1-lock*[1,1]);
   
   % Force law for the sprint between 2 neighbour QD
   F=@(L) (L-L0)/L*k;
   
   % Go through the QDs
   for i=1:length(xycoords)
       %If not locked:
       if lock(i)==0
           P=xy(i,:);
           force=zeros(6,2);
          
           % sum up the force contribution of all 6 springs connected to
           % neighbours
           for f=1:length(find(connectivity(i,:)))
               Pj=xy(connectivity(i,f),:);
               L=norm(Pj-P);
               dir=(Pj-P)/L;
               force(f,:)=F(L)*dir;
           end

           % Add the force induced by damping
           Fxy(i,:)=sum(force)-d*v(i,:);

       end
   end
   % Compute accelleration for all the QDs
   axy=Fxy/m;
end