%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% f_factor_mapping is called by the cTFM mesh generator     %
%                                                           %
% This function is used to translate user input in the      %
% GUI's factor selection to actually values. Or in to       %
% the input of a different value in an input box. The       %
% mapped/inputed value is returned.                         %
%                                                           %
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

function factor = f_factor_mapping(contents,iEntry,sCase)
%this needs to be carefully maintained such that the mapping is always
%accurate
mapping = [ %[zeile,wert]
2,0.0717;
3,0.1340;
]; %10 entries

if strcmp('set',sCase)
    %here the values of the factor are retrieved for the selection made
    [lind,ind]=ismember(iEntry,mapping(:,1));
    if lind == 1
        factor =  mapping(ind,2);      
    else
        if iEntry == 5
            prompt = {'Enter objective scaling [um/px]:',};
            dlg_title = 'Input';
            num_lines = 1;
            def = {'0'};
            answer = inputdlg(prompt,dlg_title,num_lines,def);
            factor = str2double(cell2mat(answer));
        else
            factor = -1;
        end
    end
    
elseif strcmp('get',sCase)
    %here the selection is made based on the factor that is loaded
    [lind,ind]=ismember(iEntry,mapping(:,2));
    if lind == 1
        factor =  mapping(ind,1);      
    else
        factor = 16;
    end
end

% select
% ----Cell Culture Room-----
% 60x - 1x	- 0.1075
% 60x - 1.5x	- 0.0717
% 40x - 1x	- 0.157
% 20x - 1x	- 0.331
% 
% -------Spinning Disc--------
% 60x Water 	- 1.5x  	- 0.1333
% 60x Water 	- 1 x   	- 0.2028
% 60x Oil 	- 1.5x        	- 0.1340
% 60x Oil 	- 1 x	- 0.2041
% 40x Oil 	- 1.5x	- 0.1960
% 40x Oil 	- 1x	-1.2194
% 
% 
% manual entry

