function displField_to_easy_to_use_input_data(displFieldMatPath, outputMatPath, varargin)
%DISPLFIELD_TO_EASY_TO_USE_INPUT_DATA Convert a displField struct into Easy-to-use_TFM input_data.mat format.
%
% Easy-to-use_TFM_package requires a MAT-file containing a struct named:
%   input_data
% with at least:
%   input_data.displacement(frame).pos : N×2 (x,y) in pixels
%   input_data.displacement(frame).vec : N×2 (ux,uy) in pixels
%
% This converter accepts a MAT-file containing either:
%   - displField  (preferred variable name; 1×T struct with fields pos/vec)
%   - forceField  (will NOT be used here)
% or (optionally) you can pass the variable name via 'VarName'.
%
% Optional:
%   - If you have a noise sample displacement, pass it via 'NoiseMatPath'
%     (must contain a compatible displField-like struct). Otherwise, leave
%     it empty and choose a noise ROI inside the Easy-to-use GUI.
%
% Usage:
%   displField_to_easy_to_use_input_data('canonical_displacement.mat', 'input_data_for_easy_to_use.mat');
%
%   displField_to_easy_to_use_input_data('canonical_displacement.mat', 'input_data_for_easy_to_use.mat', ...
%       'NoiseMatPath','canonical_noise.mat');

% Interactive mode (no args): choose input/output via dialogs
if nargin < 1 || isempty(displFieldMatPath)
    if usejava('desktop')
        [f,p] = uigetfile('*.mat','Select displacement MAT (contains displField)');
        if isequal(f,0), return; end
        displFieldMatPath = fullfile(p,f);
    else
        error('displFieldMatPath is required (GUI not available to prompt).');
    end
end
if nargin < 2 || isempty(outputMatPath)
    if usejava('desktop')
        defaultOut = fullfile(fileparts(displFieldMatPath),'input_data_for_easy_to_use.mat');
        [f,p] = uiputfile('*.mat','Save Easy-to-use input_data as', defaultOut);
        if isequal(f,0), return; end
        outputMatPath = fullfile(p,f);
    else
        error('outputMatPath is required (GUI not available to prompt).');
    end
end

ip = inputParser;
ip.addRequired('displFieldMatPath', @ischar);
ip.addRequired('outputMatPath', @ischar);
ip.addParameter('VarName', 'displField', @ischar);
ip.addParameter('NoiseMatPath', '', @ischar);
ip.addParameter('NoiseVarName', 'displField', @ischar);
ip.parse(displFieldMatPath, outputMatPath, varargin{:});

S = load(ip.Results.displFieldMatPath);
% If the selected MAT already contains input_data, just re-save it to the
% requested output path (helps avoid user picking the wrong file).
if isfield(S,'input_data')
    input_data = S.input_data; %#ok<NASGU>
    save(ip.Results.outputMatPath, 'input_data', '-v7');
    fprintf('Selected MAT already contained input_data. Saved to: %s\n', ip.Results.outputMatPath);
    return;
end

assert(isfield(S, ip.Results.VarName), ...
    'Variable "%s" not found in %s', ip.Results.VarName, ip.Results.displFieldMatPath);
displField = S.(ip.Results.VarName);

displField = local_normalize_displField(displField);

input_data = struct(); %#ok<NASGU>
input_data.displacement = displField; %#ok<STRNU>

% Optional noise sample
if ~isempty(ip.Results.NoiseMatPath)
    Sn = load(ip.Results.NoiseMatPath);
    assert(isfield(Sn, ip.Results.NoiseVarName), ...
        'Noise variable "%s" not found in %s', ip.Results.NoiseVarName, ip.Results.NoiseMatPath);
    noiseField = local_normalize_displField(Sn.(ip.Results.NoiseVarName));
    input_data.noise = noiseField; %#ok<STRNU>
end

save(ip.Results.outputMatPath, 'input_data', '-v7');
fprintf('Saved Easy-to-use input_data to: %s\n', ip.Results.outputMatPath);

end

function displField = local_normalize_displField(src)
% Normalize common variants into a 1×T struct array with fields pos/vec (double).

if iscell(src)
    src = [src{:}];
end
assert(isstruct(src), 'Expected struct array with fields pos/vec');
assert(all(isfield(src, {'pos','vec'})), 'Expected fields pos and vec');

T = numel(src);
displField(1,T) = struct('pos',[],'vec',[]); %#ok<AGROW>
for t = 1:T
    pos = double(src(t).pos);
    vec = double(src(t).vec);
    assert(size(pos,2) == 2, 'pos must be N×2');
    assert(size(vec,2) == 2, 'vec must be N×2');
    displField(t).pos = pos;
    displField(t).vec = vec;
end
end

