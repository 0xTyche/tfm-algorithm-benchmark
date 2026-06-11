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


function [ DotCoords0 ] = ComputeInitialPosition(UI, measurementData, PlotCurrentGrid )
% Compute the initial position of the dots using a local optimization
    
    % Define default arguments
    if nargin < 3
      PlotCurrentGrid =0;
    end

    %% identify border points and lock them (block displacement)
    
    % if the parameter fixed_frame  has length 1 -> assume isotropic
    % border definition
    border=UI.parameters.fixed_frame;
    if length(border)==1
        border=[1,1,1,1]*border;   
    end
    
    % if the parameter fixed_frame has the same length than the coordinates
    % vector, assume that the user has defined for each node if it's locked
    % or not
    if length(border)==length(measurementData.DotCoords(:,1))
        lock=border;
        border_coords=measurementData.DotCoords(find(lock),1:3);
        xy_lock=measurementData.DotCoords(find(lock),1:2);
        z0=zeros(length(measurementData.DotCoords(:,1)),1);
        z0(find(lock))=measurementData.DotCoords(find(lock),3);
    else
        % Definition of isotropic borders
        
        % initialization
        lock=zeros(length(measurementData.DotCoords(:,1)),1);
        p=1;
        z0=zeros(length(measurementData.DotCoords(:,1)),1);
        border_coords=[];
        
        % go trough all points and check if the discnce to one of the
        % borders is sufficiently small compared to the user defined borders -> lock
        
        for i=1:length(lock)
            if (measurementData.DotCoords(i,1)<min(measurementData.DotCoords(:,1))+border(4) || measurementData.DotCoords(i,1)>max(measurementData.DotCoords(:,1))-border(2) || (measurementData.DotCoords(i,2))<min(measurementData.DotCoords(:,2))+border(1) || measurementData.DotCoords(i,2)>max(measurementData.DotCoords(:,2))-border(3))
                lock(i)=1;
                xy_lock(p,:)=measurementData.DotCoords(i,1:2);
                z0(i)=measurementData.DotCoords(i,3);
                border_coords(p,:)=measurementData.DotCoords(i,1:3);
                p=p+1;
            end
        end
    end

    %% get Connectivity between Dots
    connectivity=zeros(length(measurementData.DotCoords),6);
    for i=1:length(measurementData.Triangles)
        
        triangle=measurementData.Triangles(i,:);
        k=1;
        
        if length(find(connectivity(triangle(k),:)==triangle(2)))==0 && triangle(2)~=triangle(k)
           connectivity(triangle(k),length(find(connectivity(triangle(k),:)))+1)=triangle(2);
        end
        
        if length(find(connectivity(triangle(k),:)==triangle(3)))==0 && triangle(3)~=triangle(k)
           connectivity(triangle(k),length(find(connectivity(triangle(k),:)))+1)=triangle(3);
        end
        
        k=2;
        if length(find(connectivity(triangle(k),:)==triangle(1)))==0 && triangle(1)~=triangle(k)
           connectivity(triangle(k),length(find(connectivity(triangle(k),:)))+1)=triangle(1);
        end
        
        if length(find(connectivity(triangle(k),:)==triangle(3)))==0 && triangle(3)~=triangle(k)
           connectivity(triangle(k),length(find(connectivity(triangle(k),:)))+1)=triangle(3);
        end
        
        k=3;
        if length(find(connectivity(triangle(k),:)==triangle(2)))==0 && triangle(2)~=triangle(k)
           connectivity(triangle(k),length(find(connectivity(triangle(k),:)))+1)=triangle(2);
        end
        
        if length(find(connectivity(triangle(k),:)==triangle(1)))==0 && triangle(1)~=triangle(k)
           connectivity(triangle(k),length(find(connectivity(triangle(k),:)))+1)=triangle(1);
        end
    end
    
    %% Explicit dynamic relaxation of the QD mesh
    
    % Parameters
    d=1;
    m=1;
    k=2;
    dt=.2;
    L0=measurementData.dot_distance;
    rel=1e5;
    
    % Initialize position, velocity and accelleration vectors
    xy=measurementData.DotCoords(:,1:2);
    vxy=zeros(size(measurementData.DotCoords(:,1:2)));
    axy=zeros(size(measurementData.DotCoords(:,1:2)));
   
    if PlotCurrentGrid==0
        Nsub=3;
    else
        Nsub=4;
    end
     
    figure('Units', 'normalized','Position',[0.05,0.3,0.9,0.4])
    fig = gcf;
    
    subplot(1,Nsub,1)
    scatter(xy_lock(:,1),xy_lock(:,2),'.r')
    hold on
    colormap gray
    trimesh(measurementData.Triangles,xy(:,1),xy(:,2),zeros(length(xy(:,1)),1),'FaceColor','none')
    hold on
    title('Measured Position')
    axis equal
    box on
    xlim([min(measurementData.DotCoords(:,1))-5,max(measurementData.DotCoords(:,1))+5])
    ylim([min(measurementData.DotCoords(:,2))-5,max(measurementData.DotCoords(:,2))+5])
    xlabel('x-Coordinate [\mum]')
    ylabel('y-Coordinate [\mum]')

      
    N=UI.parameters.N_max;
    display('Starting Reference Position Reconstruction...')
    fitness=zeros(N+1);
    lambda=zeros(N+1);
    [Fit,lambda]=Fitness(measurementData.Triangles,xy,L0);
    fitness(1)=Fit;
    lambda_stat(1,:)=lambda(1:3);
    
    
    subplot(1,Nsub,Nsub)

    hold on
    plot([0,N],log10(UI.parameters.Relative_threshold)*[1,1],'-.r')
    ylabel('log(Relative Threshold)')
    xlabel('Iteration') 
    title('Exit Criteria')
    xlim([0,100])
    ylim([ log10(UI.parameters.Relative_threshold)-.2,1])
    
    
    drawnow
 

    % Enter Solution Loop
    for j=1:N
        
        % Update position, velocity and accelleration with Runge-Kutta 4°
        % order Scheme
        x1 = xy;
        v1 = vxy;
        a1 = accelleration( measurementData.DotCoords(:,1:2),connectivity,lock,x1,v1,k,d,m ,L0);

        x2 = xy + 0.5*v1*dt;
        v2 = vxy + 0.5*a1*dt;
        a2 = accelleration( measurementData.DotCoords(:,1:2),connectivity,lock,x2,v2,k,d,m ,L0);
    
        x3 = xy + 0.5*v2*dt;
        v3 = vxy+ 0.5*a2*dt;
        a3 = accelleration( measurementData.DotCoords(:,1:2),connectivity,lock,x3,v3,k,d,m ,L0);
    
        x4 = xy + v3*dt;
        v4 = vxy + a3*dt;
        a4 = accelleration( measurementData.DotCoords(:,1:2),connectivity,lock,x4,v4,k,d,m ,L0);
    
        xy = xy + (dt/6.0)*(v1 + 2*v2 + 2*v3 + v4);
        vxy = vxy + (dt/6.0)*(a1 + 2*a2 + 2*a3 + a4);

        % Compute network fitness (deviation from perfect grid)
        [Fit,lambda]=Fitness(measurementData.Triangles,xy,L0);
        fitness(j+1)=Fit;
        lambda_stat(j+1,:)=lambda(1:3);
        

        % update plots
        figure(fig)
        
        if PlotCurrentGrid==1
            subplot(1,Nsub,2)
            hold off
            title(strcat('Iteration: ', num2str(j-1)))
            scatter(xy_lock(:,1),xy_lock(:,2),'.r')
            axis equal
            hold on
            colormap gray
            trimesh(measurementData.Triangles,xy(:,1),xy(:,2),zeros(length(xy(:,1)),1),'FaceColor','none')
            box on
            xlim([min(measurementData.DotCoords(:,1))-5,max(measurementData.DotCoords(:,1))+5])
            ylim([min(measurementData.DotCoords(:,2))-5,max(measurementData.DotCoords(:,2))+5])
            title('Optimized Initial Position')
            xlabel('x-Coordinate [\mum]')
            ylabel('y-Coordinate [\mum]')
        end
        
        subplot(1,Nsub,Nsub-1)
        hold on
        scatter(j,log10(fitness(j+1)),'.k')
        ylabel('log(Error)')
        xlabel('Iteration') 
        title('Grid Regularity')
        
        % Compute relative threshold 
        rel=abs(fitness(j)-fitness(j+1))/fitness(j+1);
        
        subplot(1,Nsub,Nsub)
        hold on
        scatter(j,log10(rel),'.k')
        xlim([0,j+100])
        drawnow
        
        % if threshold requirement is met-> exit
        if rel<UI.parameters.Relative_threshold
            break
        end
    end



    if rel<UI.parameters.Relative_threshold
        display('Optimization Completed! (Relative threshold has been reached)')
    else
        display('Optimization Completed! (Maximal Number of Iteration has been reached)')
    end
    
    
    
    % return reference configuration coordinates
    DotCoords0=[xy,z0];
    
    

end

