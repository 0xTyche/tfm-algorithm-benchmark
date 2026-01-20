function uinferforce_export_canonical_displacement(movieDataMatPath, outputMatPath)
%UINFERFORCE_EXPORT_CANONICAL_DISPLACEMENT Export u-inferforce displacement to canonical format.
%
% This reads a saved MovieData MAT (usually Results/movieData.mat) and
% exports the displacement field from:
%   - DisplacementFieldCorrectionProcess (preferred if present)
%   - otherwise DisplacementFieldCalculationProcess
%
% Canonical output:
%   displField(1×T) with fields:
%     - pos (N×2 double) : [x y] in pixels
%     - vec (N×2 double) : [ux uy] in pixels
%
% Example:
%   addpath(genpath('.../algorithms/matlab/u-inferforce-master/software'));
%   uinferforce_export_canonical_displacement( ...
%     '.../datasets/u-inferforce-master-datasets/Results/movieData.mat', ...
%     '.../datasets/tools/canonical_displacement_from_uinferforce.mat');

% Best-effort: temporarily add u-inferforce classes to MATLAB path (common
% source of errors when running this exporter from a different directory).
% We restore the original path on exit to avoid name-collisions (e.g.
% reg_fourier_TFM exists in multiple toolboxes).
origPath = path; %#ok<NASGU>
cleanupPath = onCleanup(@() path(origPath)); %#ok<NASGU>

try
    thisFileDir = fileparts(mfilename('fullpath')); % .../datasets/tools
    repoRoot = fileparts(fileparts(thisFileDir));   % .../tfm-algorithm-benchmark
    uinferforceSoftwareDir = fullfile(repoRoot,'algorithms','matlab','u-inferforce-master','software');
    if exist(uinferforceSoftwareDir,'dir') == 7
        addpath(genpath(uinferforceSoftwareDir), '-begin');
        rehash;
    end
catch
    % Ignore: user may run from elsewhere; we'll error with guidance later.
end

% Interactive mode (no args): pop up file pickers.
if nargin < 1 || isempty(movieDataMatPath)
    if usejava('desktop')
        [f,p] = uigetfile('*.mat','Select u-inferforce MovieData MAT (e.g. movieData.mat)');
        if isequal(f,0)
            return;
        end
        movieDataMatPath = fullfile(p,f);
    else
        error('movieDataMatPath is required (GUI not available to prompt).');
    end
end
if nargin < 2 || isempty(outputMatPath)
    if usejava('desktop')
        defaultOut = fullfile(fileparts(movieDataMatPath),'canonical_displacement.mat');
        [f,p] = uiputfile('*.mat','Save canonical displacement as', defaultOut);
        if isequal(f,0)
            return;
        end
        outputMatPath = fullfile(p,f);
    else
        error('outputMatPath is required (GUI not available to prompt).');
    end
end

S = load(movieDataMatPath);
fn = fieldnames(S);

MD = [];
for i = 1:numel(fn)
    v = S.(fn{i});
    if isa(v,'MovieData')
        MD = v;
        break
    end
end
assert(~isempty(MD), ...
    ['No MovieData object found in MAT-file. ' ...
     'Make sure u-inferforce software is on the MATLAB path, then re-run.']);

% Guard against missing/incorrect MovieData class on path (common when the
% MAT-file is loaded without adding u-inferforce software, or when a
% different MovieData implementation shadows it).
if ~ismethod(MD,'getProcessIndex')
    error(['Loaded a MovieData object, but method getProcessIndex is missing.\n' ...
        'This usually means u-inferforce classes are NOT on the MATLAB path, or are shadowed by another toolbox.\n\n' ...
        'Fix:\n' ...
        '  1) addpath(genpath(''%s''));\n' ...
        '  2) rehash; clear classes;\n' ...
        '  3) run: which MovieData -all  (ensure it points to .../u-inferforce-master/software/@MovieData)\n' ...
        '  4) re-run this exporter.\n'], ...
        fullfile('algorithms','matlab','u-inferforce-master','software'));
end

% Prefer corrected displacement field if available
iProc = MD.getProcessIndex('DisplacementFieldCorrectionProcess',1,0);
if isempty(iProc)
    iProc = MD.getProcessIndex('DisplacementFieldCalculationProcess',1,0);
end
assert(~isempty(iProc), 'No displacement process found in MovieData');

proc = MD.processes_{iProc};
assert(proc.checkChannelOutput(), 'Displacement process output not found on disk');

displField = proc.loadChannelOutput; %#ok<NASGU>
meta = struct(); %#ok<NASGU>
meta.source = 'u-inferforce MovieData displacement process output';
meta.movieDataMatPath = movieDataMatPath;
meta.processName = class(proc);
meta.units = 'pixels';
try
    meta.pixelSize_nm = MD.pixelSize_;
    meta.timeInterval_s = MD.timeInterval_;
catch
end

save(outputMatPath,'displField','meta','-v7');
fprintf('Saved canonical displacement to: %s\n', outputMatPath);

end

