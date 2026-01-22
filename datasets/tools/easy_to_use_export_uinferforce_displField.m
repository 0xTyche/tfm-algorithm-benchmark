function easy_to_use_export_uinferforce_displField(inputDataMatPath, outputDisplFieldMatPath)
%EASY_TO_USE_EXPORT_UINFERFORCE_DISPLFIELD Convert Easy-to-use input_data.mat to u-inferforce displField.mat.
%
% Easy-to-use input:
%   input_data.displacement(frame).pos / .vec   (pixels)
%
% u-inferforce displacement process expects a MAT-file containing:
%   displField(frame).pos / .vec               (pixels)
%
% Notes (important):
% - This only converts the *displacement field data structure*.
% - To run u-inferforce Step 4/5 using this, your MovieData (image size,
%   ROI mask, pixel size) must be compatible with the displacement domain.
%
% Interactive usage:
%   easy_to_use_export_uinferforce_displField

if nargin < 1 || isempty(inputDataMatPath)
    if usejava('desktop')
        [f,p] = uigetfile('*.mat','Select Easy-to-use input_data.mat');
        if isequal(f,0), return; end
        inputDataMatPath = fullfile(p,f);
    else
        error('inputDataMatPath is required (GUI not available to prompt).');
    end
end
if nargin < 2 || isempty(outputDisplFieldMatPath)
    if usejava('desktop')
        [f,p] = uiputfile('*.mat','Save u-inferforce displField.mat as','displField.mat');
        if isequal(f,0), return; end
        outputDisplFieldMatPath = fullfile(p,f);
    else
        error('outputDisplFieldMatPath is required (GUI not available to prompt).');
    end
end

S = load(inputDataMatPath);
assert(isfield(S,'input_data'), 'Input MAT must contain struct variable ''input_data''.');
assert(isfield(S.input_data,'displacement'), 'input_data must contain field ''displacement''.');

src = S.input_data.displacement;
assert(isstruct(src) && all(isfield(src,{'pos','vec'})), 'input_data.displacement must be struct array with pos/vec.');

displField = src; %#ok<NASGU>
save(outputDisplFieldMatPath,'displField','-v7.3');
fprintf('Saved u-inferforce displField to: %s\n', outputDisplFieldMatPath);

end

