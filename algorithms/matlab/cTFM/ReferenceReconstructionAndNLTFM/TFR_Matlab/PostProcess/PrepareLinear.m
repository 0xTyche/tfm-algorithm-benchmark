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




function [ T_out ] =PrepareLinear( P,T )
    T_renum=zeros(size(T));
    t=0;
    for i=1:length(T)
       T_row=T(i,:);
       P_index=zeros(1,3);

       for j=1:length(T_row)
          fnd=find(P(:,1)==T_row(j));
          if length(fnd)==1 
              P_index(j)=fnd;
          else
              break
          end

       end
       if length(find(P_index==0))==0
           t=t+1;          
           T_renum(t,:)=P_index;
       end
    end
    
    T_out=T_renum(1:t,:);


end

