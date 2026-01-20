% Copyright (C) 2010 - 2019, Sabass Lab
%
% This program is free software: you can redistribute it and/or modify it 
% under the terms of the GNU General Public License as published by the Free
% Software Foundation, either version 3 of the License, or (at your option) 
% any later version. This program is distributed in the hope that it will be 
% useful, but WITHOUT ANY WARRANTY; without even the implied warranty of 
% MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General 
% Public License for more details. You should have received a copy of the 
% GNU General Public License along with this program.
% If not, see <http://www.gnu.org/licenses/>.


function TF_reconstruction
     where_am_I = mfilename('fullpath');
     [my_directory,name] = fileparts(where_am_I);
     % Ensure THIS toolbox takes precedence on the MATLAB path.
     % (reg_fourier_TFM exists in other TFM toolboxes; appending this folder
     % can lead to calling the wrong function signature.)
     addpath(my_directory,'-begin');
     rehash;
     clear('reg_fourier_TFM'); % clear cached resolution after path change
    get_data;
end