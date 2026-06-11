%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% f_savecheck is called by the cTFM mesh generator          %
%                                                           %
% This function is called by f_save to check whether a data %
% is already available in which case it will ask to         %
% overwrite before saving.                                  %
%                                                           %
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

function pass = f_savecheck(var,sCase)
%check existence of directory
if exist([var.ImageFolder,'/',var.ImageName],'dir')==0
    %create directory if needed
    mkdir(var.ImageFolder,var.ImageName)
end
switch sCase
    case 'nodes'
        %check existence of mat and prompt to overwrite if necessary
        if exist([var.ImageFolder,'/',var.ImageName,'/nodes.mat'],'file')
            %file exists
            pass = 0;
        else
            pass = 1;
        end
    case 'mesh'
        %check existence of mat and prompt to overwrite if necessary
        if exist([var.ImageFolder,'/',var.ImageName,'/mesh.mat'],'file')
            %file exists
            pass = 0;
        else
            pass = 1;
        end
    case 'strain'
                %check existence of mat and prompt to overwrite if necessary
        if exist([var.ImageFolder,'/',var.ImageName,'/strain.mat'],'file')
            %file exists
            pass = 0;
        else
            pass = 1;
        end
    case 'stress'
                %check existence of mat and prompt to overwrite if necessary
        if exist([var.ImageFolder,'/',var.ImageName,'/stress.mat'],'file')
            %file exists
            pass = 0;
        else
            pass = 1;
        end        
    otherwise
        pass = -1;
end
