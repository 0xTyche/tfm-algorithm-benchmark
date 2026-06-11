function result = tfmlab_fix_dipimage(dipRoot)
%TFMLAB_FIX_DIPIMAGE One-click DIPimage repair for TFMLAB beginners.
%
% Usage:
%   tfmlab_fix_dipimage
%   tfmlab_fix_dipimage('C:\tools\dipimage_3.2_windows_fftw')
%
% What this script does:
%   0) fix bug
%   1) Resets MATLAB path for a clean start (session only)
%   2) Adds TFMLAB folders back to path
%   3) Finds a complete DIPimage installation
%   4) Adds DIPimage MATLAB path + DLL folders to PATH
%   5) Verifies dip_math MEX by running stretch(rand(32))
%
% Notes:
%   - This script does not install software.
%   - If Visual C++ runtime is missing, MEX can still fail to load.

if nargin < 1
    dipRoot = '';
end

result = struct();
result.ok = false;
result.message = '';
result.projectRoot = '';
result.dipRoot = '';
result.whichDipMath = '';
result.dllDirsAdded = {};

fprintf('\nTFMLAB one-click DIPimage repair\n');
fprintf('================================\n');

projectRoot = fileparts(mfilename('fullpath'));
result.projectRoot = projectRoot;
fprintf('Project root: %s\n', projectRoot);

% 1) Reset path to avoid stale/duplicate old copies.
fprintf('\n[1/5] Resetting MATLAB path (session only)...\n');
restoredefaultpath;
rehash toolboxcache;
clear mex;

% 2) Add TFMLAB paths.
fprintf('[2/5] Adding TFMLAB folders...\n');
addpath(genpath(projectRoot));
bfFolder = fullfile(projectRoot, 'bfmatlab');
if isfolder(bfFolder)
    addpath(genpath(bfFolder));
end

% 3) Find complete DIPimage installation.
fprintf('[3/5] Locating a complete DIPimage installation...\n');

candidateRoots = {};
if ~isempty(dipRoot)
    candidateRoots{end+1} = dipRoot; %#ok<AGROW>
end
candidateRoots{end+1} = fullfile(projectRoot, 'dipimage_3.2_windows_fftw');
candidateRoots{end+1} = 'C:\tools\dipimage_3.2_windows_fftw';
candidateRoots{end+1} = 'C:\DIPimage';
candidateRoots = unique(candidateRoots, 'stable');

chosenRoot = '';
lastReason = '';
for i = 1:numel(candidateRoots)
    root = candidateRoots{i};
    [ok, reason] = i_is_complete_dipimage(root);
    if ok
        chosenRoot = root;
        break;
    end
    if ~isempty(reason)
        lastReason = reason;
    end
end

if isempty(chosenRoot)
    fprintf('No complete DIPimage found in default locations.\n');
    if ~isempty(lastReason)
        fprintf('Last check detail: %s\n', lastReason);
    end
    if usejava('desktop')
        selected = uigetdir(projectRoot, ...
            'Select your DIPimage folder (the folder that contains diplib)');
        if isequal(selected, 0)
            result.message = 'Cancelled by user (no DIPimage folder selected).';
            fprintf('[FAIL] %s\n\n', result.message);
            return;
        end
        [ok, reason] = i_is_complete_dipimage(selected);
        if ~ok
            result.message = ['Selected folder is not a complete DIPimage package: ', reason];
            fprintf('[FAIL] %s\n\n', result.message);
            return;
        end
        chosenRoot = selected;
    else
        result.message = ['No complete DIPimage found automatically. ', ...
            'Run this function again with a folder path argument.'];
        fprintf('[FAIL] %s\n\n', result.message);
        return;
    end
end

result.dipRoot = chosenRoot;
fprintf('Using DIPimage folder: %s\n', chosenRoot);

% 4) Add DIPimage MATLAB path and likely DLL directories.
fprintf('[4/5] Adding DIPimage paths and DLL folders...\n');
dipShare = fullfile(chosenRoot, 'diplib', 'share', 'DIPimage');
addpath(genpath(dipShare));

dllDirs = i_existing_dll_dirs(chosenRoot);
for i = 1:numel(dllDirs)
    i_prepend_to_path(dllDirs{i});
end
result.dllDirsAdded = dllDirs;

rehash toolboxcache;
clear mex;

% 5) Verify by loading dip_math through stretch.
fprintf('[5/5] Running verification test (stretch(rand(32)))...\n');
result.whichDipMath = which('dip_math');
if isempty(result.whichDipMath)
    result.message = 'dip_math is still not visible on MATLAB path.';
    fprintf('[FAIL] %s\n', result.message);
    fprintf('Tip: check if DIPimage/private folder is present and readable.\n\n');
    return;
end

fprintf('dip_math resolved to: %s\n', result.whichDipMath);

try
    a = rand(32);
    b = stretch(a); %#ok<NASGU>
catch ME
    result.message = sprintf(['MEX load test failed.\n', ...
        'Error: %s\n', ...
        'Most likely missing dependency: Microsoft Visual C++ Redistributable x64 (2015-2022).'], ...
        ME.message);
    fprintf('[FAIL] %s\n\n', result.message);
    return;
end

result.ok = true;
result.message = 'DIPimage MEX test passed. You can run main.m now.';
fprintf('[OK] %s\n\n', result.message);

end

function [ok, reason] = i_is_complete_dipimage(root)
ok = false;
reason = '';
if isempty(root) || ~isfolder(root)
    reason = 'Folder does not exist.';
    return;
end

sharePath = fullfile(root, 'diplib', 'share', 'DIPimage');
mexPath = fullfile(sharePath, 'private', ['dip_math.', mexext]);
if ~isfolder(sharePath)
    reason = 'Missing diplib/share/DIPimage.';
    return;
end
if ~isfile(mexPath)
    reason = ['Missing MEX file: ', mexPath];
    return;
end

dllDirs = i_existing_dll_dirs(root);
if isempty(dllDirs)
    reason = 'No likely DLL directories found (bin/lib). Package may be incomplete.';
    return;
end

% At least one DLL should exist in detected bin/lib folders.
dllCount = 0;
for i = 1:numel(dllDirs)
    dllCount = dllCount + numel(dir(fullfile(dllDirs{i}, '*.dll')));
end
if dllCount < 1
    reason = 'No DLL files found in detected bin/lib folders.';
    return;
end

ok = true;
end

function dirs = i_existing_dll_dirs(root)
candidates = {
    fullfile(root, 'bin')
    fullfile(root, 'diplib', 'bin')
    fullfile(root, 'lib')
    fullfile(root, 'diplib', 'lib')
};
dirs = {};
for i = 1:numel(candidates)
    if isfolder(candidates{i})
        dirs{end+1} = candidates{i}; %#ok<AGROW>
    end
end
end

function i_prepend_to_path(folderPath)
oldPath = getenv('PATH');
if isempty(oldPath)
    setenv('PATH', folderPath);
    return;
end
parts = regexp(oldPath, ';', 'split');
if any(strcmpi(parts, folderPath))
    return;
end
setenv('PATH', [folderPath, ';', oldPath]);
end
