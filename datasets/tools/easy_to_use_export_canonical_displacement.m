function easy_to_use_export_canonical_displacement(inputMatPath, outputMatPath)
%EASY_TO_USE_EXPORT_CANONICAL_DISPLACEMENT Export Easy-to-use displacement MAT to canonical format.
%
% Canonical output:
%   displField(1×T) with fields:
%     - pos (N×2 double) : [x y] in pixels
%     - vec (N×2 double) : [ux uy] in pixels
%
% Optional:
%   noiseField(1×T) with same fields if present.
%   meta struct describing source.
%
% Example:
%   easy_to_use_export_canonical_displacement( ...
%     fullfile(pwd,'..','Easy-to-use-TFM-datasets','dotmatdata','input_data.mat'), ...
%     fullfile(pwd,'canonical_displacement.mat'));

if nargin < 1 || isempty(inputMatPath)
    error('inputMatPath is required');
end
if nargin < 2 || isempty(outputMatPath)
    error('outputMatPath is required');
end

S = load(inputMatPath);
assert(isfield(S,'input_data'), 'Expected variable ''input_data'' in %s', inputMatPath);

idata = S.input_data;
assert(isfield(idata,'displacement'), 'input_data.displacement missing in %s', inputMatPath);

displField = local_to_displField(idata.displacement); %#ok<NASGU>

noiseField = []; %#ok<NASGU>
if isfield(idata,'noise') && ~isempty(idata.noise)
    try
        noiseField = local_to_displField(idata.noise); %#ok<NASGU>
    catch
        % Noise format varies; keep best-effort.
        noiseField = []; %#ok<NASGU>
    end
end

meta = struct(); %#ok<NASGU>
meta.source = 'Easy-to-use-TFM-datasets/dotmatdata/input_data.mat';
meta.inputMatPath = inputMatPath;
meta.units = 'pixels';
meta.notes = 'displField exported from input_data.displacement (pos/vec).';

save(outputMatPath,'displField','noiseField','meta','-v7');
fprintf('Saved canonical displacement to: %s\n', outputMatPath);

end

function displField = local_to_displField(src)
% Accept 1×T struct array or cell-like and normalize into 1×T struct array.

if iscell(src)
    src = [src{:}];
end

assert(isstruct(src), 'Expected struct array with fields pos/vec');
assert(all(isfield(src,{'pos','vec'})), 'Expected fields pos and vec');

T = numel(src);
displField(1,T) = struct('pos',[],'vec',[]); %#ok<AGROW>
for t = 1:T
    pos = double(src(t).pos);
    vec = double(src(t).vec);
    assert(size(pos,2)==2, 'pos must be N×2');
    assert(size(vec,2)==2, 'vec must be N×2');
    displField(t).pos = pos;
    displField(t).vec = vec;
end

end

