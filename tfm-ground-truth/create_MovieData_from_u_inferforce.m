% create_MovieData_from_u_inferforce.m
% Helper script for DanuserLab TFM_Package compatibility.
%
% Goal:
%   Create a real MovieData object in MATLAB and save as MovieData.mat.
%   Keep u-inferforce displacement in u_inferforce.mat for downstream workflows.
%
% How to use:
%   1) Put this script in the same folder as u_inferforce.mat
%   2) Edit imagePath/outputDir below
%   3) Run this script in MATLAB
%
% Notes:
%   - MovieData class must be on MATLAB path (from TFM_Package / u-track etc.)
%   - Python cannot directly serialize MATLAB class objects, hence this script.

clear; clc;

% === TODO: set your image path ===
% Example:
% imagePath = 'reference.tif';
% imagePath = 'C:/data/my_movie.tif';
imagePath = 'reference.tif';

% === Output directory ===
outputDir = pwd;

% Create MovieData
% For tif: MD = MovieData('image.tif', true, outputDir);
% For other inputs, see MovieData constructor help.
MD = MovieData(imagePath, true, outputDir);

% Optional metadata (recommended)
% MD.pixelSize_ = <your_pixel_size_nm>; % nm
% MD.timeInterval_ = <your_time_interval_s>; % s

% Save MovieData
save(fullfile(outputDir, 'MovieData.mat'), 'MD');
disp(['Saved MovieData to: ' fullfile(outputDir, 'MovieData.mat')]);

% Load u-inferforce displacement
uFile = fullfile(outputDir, 'u_inferforce.mat');
if exist(uFile, 'file') == 2
    S = load(uFile);
    if isfield(S, 'u')
        disp('Loaded u-inferforce displacement: S.u(1).pos / S.u(1).vec');
    elseif isfield(S, 'displacementField')
        disp('Loaded u-inferforce displacement: S.displacementField(1).pos / .vec');
    else
        disp('Loaded u-inferforce file, but did not find u/displacementField variables.');
    end
else
    warning('u-inferforce file not found: %s', uFile);
end

disp('Done.');
