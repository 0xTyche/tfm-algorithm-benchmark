%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% f_axis_control is called by the cTFM mesh generator       %
%                                                           %
% This function checks the settings on display control for  %
% the plot. It then generates the plot accordingly          %
%                                                           %
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

function f_axis_control(varargin)
hold off
fresh = 0;
handles = varargin{1};
if length(varargin) == 1 %no additional handles
    %image
    if handles.ctfm_disp_image.Value == 1
        fresh = 1;
        imshow(handles.var.img,[])
        view(2) 
    end

    %nodes
    if handles.ctfm_disp_nodes.Value == 1
        if fresh == 1
            hold on
        end
        fresh = 1;
        scatter(handles.var.xcoords,handles.var.ycoords)
        view(2) 
        set(handles.axes_image,'Ydir','reverse')
    end
    
    %nodes3d
    if handles.ctfm_disp_nodes3D.Value == 1
        if fresh == 1
            hold on
        end
        fresh = 1;
        scatter3(handles.var.xcoords,handles.var.ycoords,handles.var.zcoords*10,9,handles.var.zcoords*10)
        colormap(jet);
        set(handles.axes_image,'Ydir','reverse')
    end

    %mesh
    if handles.ctfm_disp_mesh.Value == 1
        if fresh == 1
            hold on
        end
        plot(handles.var.xcoords(1),handles.var.ycoords(1))
        hold on
        fresh = 1;
        for i = 1:length(handles.var.hex_index)
            tmp = handles.var.hex_index(i,:);
            tmp(tmp ~= 0) = 1;
            N = sum(tmp);

            line([handles.var.xcoords(i)*ones(N,1)';handles.var.xcoords(handles.var.hex_index(i,1:N))'],...
                [handles.var.ycoords(i)*ones(N,1)';handles.var.ycoords(handles.var.hex_index(i,1:N))'],'Color','b')
        end
        view(2)
        set(handles.axes_image,'Ydir','reverse')
    end

else %additional handle in varargin
    sCase = varargin{2};
    switch sCase
        case 'manual_conn'
            imshow(handles.var.img,[])
            hold on
            scatter(handles.var.xcoords,handles.var.ycoords)
%             for i = 1:length(handles.var.xcoords)
%                 tmp = handles.var.hex_index(i,:);
%                 tmp(tmp ~= 0) = 1;
%                 N = sum(tmp);
% 
%                 line([handles.var.xcoords(i)*ones(N,1)';handles.var.xcoords(handles.var.hex_index(i,1:N))'],...
%                     [handles.var.ycoords(i)*ones(N,1)';handles.var.ycoords(handles.var.hex_index(i,1:N))'],'Color','b')
%             end
            
            for i = 1:size(handles.var.manual_conn,1)
                line([handles.var.xcoords(handles.var.manual_conn(i,1)),handles.var.xcoords(handles.var.manual_conn(i,2))],...
                   [handles.var.ycoords(handles.var.manual_conn(i,1)),handles.var.ycoords(handles.var.manual_conn(i,2))]...
                   ,'Color','m')
            end
            
        case 'strain'
            hold off
            colormap('jet')
            imagesc(handles.var.strain)
            pos = get(gca,'position');
            h = colorbar('position',[pos(1)+pos(3)-0.05 pos(2) 0.015 pos(4)]);
            ylabel(h, 'Magnitude of the principle strains: $\epsilon_{max}$',...
                'interpreter','latex','FontSize',12)
            
        case 'stress'
            range=[min(min(handles.var.stress)),max(max(handles.var.stress))];
%             if range(2) > 1
%                 range(2) = 1;
%             end
            hold off
            colormap('jet')
            imagesc(handles.var.stress)
            pos = get(gca,'position');
            caxis([range(1) range(2)])
            h = colorbar('position',[pos(1)+pos(3)-0.05 pos(2) 0.015 pos(4)]);
            ylabel(h, 'Maximum principal Cauchy stress: $\sigma_{max}$',...
                'interpreter','latex','FontSize',12)            
    end
end

%this is used to keep the zoom after a node has been deleted
xLimits = get(gca,'XLim');  % Get the range of the x axis
yLimits = get(gca,'YLim');  % Get the range of the y axis

%plot handling
%axis([xLimits(1) xLimits(2) yLimits(1) yLimits(2)])
axis equal
axis off
title(handles.axes_image, handles.var.FullImageName, 'FontSize', 12, 'Interpreter', 'none');
