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


function [ T_out ] = PrepareQuadratic( P,T )
    T_renum=zeros(size(T));
    t=0;
    for i=1:length(T)
       T_row=T(i,:);
       P_index=zeros(1,6);

       for j=1:length(T_row)
          fnd=find(P(:,1)==T_row(j));
          if length(fnd)==1 
              P_index(j)=fnd;
          else
              break
          end

       end
       % Sort nodes
       if length(find(P_index==0))==0
           t=t+1;

           center=mean([P(P_index,2),P(P_index,3)]);

           angles=atan2d(P(P_index,3)-center(2),P(P_index,2)-center(1));
           [B,I] = sort(angles-angles(1));

           I=circshift(I,-(find(I==1)-1));
           T_renum(t,:)=P_index(I);

       end
    end

    T_renum=T_renum(1:t,:);


    T_p=[T_renum(:,1),T_renum(:,3),T_renum(:,5)];
    T_tri=zeros(length(T_renum)*4,3);

    for i=1:length(T_renum)
       T_row=T_renum(i,:);
       T_tri((i-1)*4+1,:)=[T_row(1),T_row(2),T_row(6)];
       T_tri((i-1)*4+2,:)=[T_row(2),T_row(4),T_row(6)];
       T_tri((i-1)*4+3,:)=[T_row(2),T_row(3),T_row(4)];
       T_tri((i-1)*4+4,:)=[T_row(6),T_row(4),T_row(5)];
    end

    T_out=T_tri
end

