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


function PlotTractionFields( job_name, shift_back,units, deformed)
% Plots all available components of the reconstructed traction field

% Define default arguments
    if nargin < 2
      shift_back=0;
    end
    
    if nargin < 3
      units='kPa';
    end
    
    if strcmp(units,'kPa')
        unit_factor=1000;
    else
        units='MPa';
        unit_factor=1  ;
    end

    if nargin < 4
      deformed=1;
    end

    % Load postprocessed Data
    R=load(['ReconstructedData/ReactionForces/', job_name]);
    R=R.Results;
    UD=load(['PreparedData/', job_name '_UserData']);
  
    % Chose data to plot (default is deformed configuration)
    if deformed ==1
        XYZ=R.P_Def;
        Traction=R.Traction_triangle_Def;
    else
        XYZ=R.P;
        Traction=R.Traction_triangle;
    end
    
    

    % Chekh if the coordinate system has been moved to the center of the
    % image durin preprocessing. If asked, shift back to image corner
    if length(find(R.P(:,2)<0))>0 && length(find(R.P(:,3)<0))>0
        Recentered=1;
        if shift_back==1
            Recentered=0;
            XYZ(:,2)=XYZ(:,2)+UD.ImageSize(2)*UD.image_scaling/2;
            XYZ(:,3)=XYZ(:,3)+UD.ImageSize(1)*UD.image_scaling/2;
        end
    else
        Recentered=0;
    end
    
    
    % Are there traction components in Z-direction or was the third
    % direction unconstrained? if unconstrained, plot only x and y
    % components + magnitude
    if length(find(Traction(:,3)~=0))==0
        N=2;
    else
        N=3;
    end
        
    % Make traction stress plots for the single components
    coordinates='xyz';
    for i=1:N
        hFig = figure();

        hold on
        axis equal
        set(gca,'FontSize',12)
        h=trisurf(R.T,XYZ(:,2),XYZ(:,3),XYZ(:,4),Traction(:,i)*unit_factor);

        fill(([0,1,1,0,0]-Recentered*0.5)*UD.ImageSize(2)*UD.image_scaling,([0,0,1,1, 0 ]-Recentered*0.5)*UD.ImageSize(1)*UD.image_scaling,0,'EdgeColor','none');
        set(h, 'edgecolor','none')

        xlabel('x-Coordinate [\mum]')
        ylabel('y-Coordinate [\mum]')
        title(['Traction Field (' coordinates(i) '-Component)'])
        c=colorbar();
        zlab = get(c,'ylabel');
        set(zlab,'String',units); 
        xlim(([0 1]-Recentered*0.5)*UD.ImageSize(2)*UD.image_scaling)
        ylim(([0 1]-Recentered*0.5)*UD.ImageSize(1)*UD.image_scaling)
        box on
        if i==3
            colormap hot
            
            % Plot In-Plane Magnitude of the traction field
            Traction_Mag_InPlane= (Traction(:,1).^2+Traction(:,2).^2).^.5;
            hFig = figure();

            hold on
            axis equal
            set(gca,'FontSize',12)
            h=trisurf(R.T,XYZ(:,2),XYZ(:,3),XYZ(:,4),Traction_Mag_InPlane*unit_factor);

            fill(([0,1,1,0,0]-Recentered*0.5)*UD.ImageSize(2)*UD.image_scaling,([0,0,1,1, 0 ]-Recentered*0.5)*UD.ImageSize(1)*UD.image_scaling,0,'EdgeColor','none');
            set(h, 'edgecolor','none')

            xlabel('x-Coordinate [\mum]')
            ylabel('y-Coordinate [\mum]')
            title(['Traction Field (In-Plane Magnitude)'])
            c=colorbar();
            zlab = get(c,'ylabel');
            set(zlab,'String',units); 
            xlim(([0 1]-Recentered*0.5)*UD.ImageSize(2)*UD.image_scaling)
            ylim(([0 1]-Recentered*0.5)*UD.ImageSize(1)*UD.image_scaling)
            box on
            colormap jet
            
        else
            colormap jet
        end
        


        
        
    end
    
    % Plot Magnitude of the traction field
    Traction_Mag= (Traction(:,1).^2+Traction(:,2).^2+Traction(:,3).^2).^.5;
    hFig = figure();
    
    hold on
    axis equal
    set(gca,'FontSize',12)
    h=trisurf(R.T,XYZ(:,2),XYZ(:,3),XYZ(:,4),Traction_Mag*unit_factor);

    fill(([0,1,1,0,0]-Recentered*0.5)*UD.ImageSize(2)*UD.image_scaling,([0,0,1,1, 0 ]-Recentered*0.5)*UD.ImageSize(1)*UD.image_scaling,0,'EdgeColor','none');
    set(h, 'edgecolor','none')

    xlabel('x-Coordinate [\mum]')
    ylabel('y-Coordinate [\mum]')
    title(['Traction Field (Magnitude)'])
    c=colorbar();
    zlab = get(c,'ylabel');
    set(zlab,'String',units); 
    xlim(([0 1]-Recentered*0.5)*UD.ImageSize(2)*UD.image_scaling)
    ylim(([0 1]-Recentered*0.5)*UD.ImageSize(1)*UD.image_scaling)
    box on
    colormap jet

end

