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



function  Results=PostProcess( job_name)
% Postprocessing method for the reconstruction of the traction field out of
% the nodal reaction forces and the mesh data
    

    %% Load  reaction forces and mesh data
    fname=strcat(job_name,'.txt');
    P=load(strcat('MeshData/',job_name,'_Nodes.txt'));
    T=load(strcat('MeshData/',job_name,'_Elements.txt'));
    F=load(strcat('ReconstructedData/ReactionForces/',fname));
   
    
    P_f=zeros(size(P));
    p=0;
    
    for i=1:length(P)
        if length(find(F(:,1)==P(i,1)))
            p=p+1;
            P_f(p,:)=P(i,:);
        end
        

    end
    P=P_f(1:p,:);
    
    % Control that all the vertices of the triagles are defined
    % For quadratic meshes, the 6 noded element faces have to be split in 6
    % triangles
    if length(T(1,:))==3
        T=PrepareLinear(P,T);
    else
        T=PrepareQuadratic(P,T);
    end
    

    %% Compute grometrical properties of the triangles
    
    % Initialize Arrays
    T_area=zeros(length(T),2); % Triangle area in undeformed and deformed configuration
    T_Def=zeros(length(T),3); % Displacement of the center of gravity of triangle 

    for t=1:length(T)
        
        % Compute Area (Undeformed)
        v1=P(T(t,2),2:4)-P(T(t,1),2:4);
        v2=P(T(t,3),2:4)-P(T(t,1),2:4);
        T_area(t,1)=norm(cross(v1,v2))/2;
        
         % Compute Area (Deformed)
        v1=(P(T(t,2),2:4)+F(T(t,2),2:4))-(P(T(t,1),2:4)+F(T(t,1),2:4));
        v2=(P(T(t,3),2:4)+F(T(t,3),2:4))-(P(T(t,1),2:4)+F(T(t,1),2:4));
        T_area(t,2)=norm(cross(v1,v2))/2;
        
        % Displacement of the center of gravity
        T_Def(t,:)=mean(F(T(t,:),2:4));
        
    end
    
    % Compute the trianglw areas to each point  (sum of all triangle that share the point)
    P_area=zeros(length(P),2);
    for t=1:length(P)
        
        % Find Triagles
        tr1=find(T(:,1)==t);
        tr2=find(T(:,2)==t);
        tr3=find(T(:,3)==t);

        % Point associated Area in the undeformed config
        P_area(t,1)=sum([T_area(tr1,1)',T_area(tr2,1)',T_area(tr3,1)']);
        if P_area(t,1)==0    
            P_area(t,1)=NaN;
        end
        
        % Point associated Area in the deformed config
        P_area(t,2)=sum([T_area(tr1,2)',T_area(tr2,2)',T_area(tr3,2)']);
        if P_area(t,2)==0    
            P_area(t,2)=NaN;
        end
    end

  
    %% Compute traction stresses on the subtrate's surface
    
    % Compute the smeared reaction forces at the nodes
    % defined as the reaction force divided through the area of all
    % connected surface element faces
    SmearedReactionForces=F(:,5:7)./(P_area(:,1)*[1,1,1]);
    SmearedReactionForces_Def=F(:,5:7)./(P_area(:,2)*[1,1,1]);

    % Compute  stresses in the triangles (contribution from all the nodes of the triangle)
    for t=1:length(T)
        T_t(t,:)=sum(SmearedReactionForces(T(t,:),:));
        T_t_Def(t,:)=sum(SmearedReactionForces_Def(T(t,:),:));
    end
    
    % Traction stresses at the nodes (undeformed and deformed)
    % the factor 3 is due to the fact that each triangle is connected to
    % three nodes, therefore the area of related to is only 1/3 of the
    % total area of all connected surface triangles (1/(1/3) -> *3)
    Traction=SmearedReactionForces_Def*3;
    Traction_Def=SmearedReactionForces_Def*3;
    

    % Point position in deformed configuration
    P_def= P;
    P_def(:,2:4)= P_def(:,2:4)+F(:,2:4);
     
    %Save Traction fields
    Results=struct('F',F,'P',P,'P_Def',P_def,'T',T,'Traction_triangle',T_t,'Traction_triangle_Def',T_t_Def,'T_Def',T_Def,'T_Area',T_area,'Traction',Traction,'Traction_Def',Traction_Def);
    save(strcat('ReconstructedData/ReactionForces/',job_name),'Results')

end

