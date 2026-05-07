function easy_to_use_input_data_to_uinferforce_movieData(inputDataMatPath, outMovieDataMatPath, varargin)
%EASY_TO_USE_INPUT_DATA_TO_UINFERFORCE_MOVIEDATA
% Convert Easy-to-use_TFM_package input_data.mat into a minimal u-inferforce MovieData project (movieData.mat).
%
% Why this exists:
% - Easy-to-use works from displacement structs (input_data.displacement.pos/vec).
% - u-inferforce stores a full "MovieData" object (movieData.mat) and expects a displacement process output displField.mat.
% - If you only have displacement (no raw bead images), we can still run u-inferforce force reconstruction by creating:
%   (1) a dummy image series (blank tifs) to define image dimensions
%   (2) a MovieData object pointing to that image series
%   (3) a DisplacementFieldCalculationProcess whose outFilePaths points to a saved displField.mat
%
% Inputs:
% - inputDataMatPath: path to Easy-to-use input_data.mat (must contain variable "input_data")
% - outMovieDataMatPath: where to save u-inferforce MovieData MAT, e.g. ".../Results/movieData.mat"
%
% Options (name/value):
% - 'PixelSize_um' (required): micrometers per pixel (e.g. 0.108)
% - 'TimeInterval_s' (optional): seconds between frames (default: [])
% - 'NumAperture' (optional): numerical aperture (default: [])
% - 'CamBitdepth' (optional): camera bit depth (default: 16)
% - 'Fluorophore' (optional): e.g. 'GFP' (default: '')
% - 'Excitation_nm' (optional): e.g. 488 (default: [])
% - 'Emission_nm' (optional): e.g. 507 (default: [])
% - 'Exposure_ms' (optional): e.g. 50 (default: [])
% - 'ImageSize_px' (optional): [height width]. If omitted, inferred from max(pos) across frames (+margin).
% - 'DummyImageDir' (optional): folder to write dummy tifs. Default: alongside movieData.mat as "dummy_beads_images".
% - 'OverwriteDummyImages' (optional): true/false (default: false)
% - 'DummyImageMode' (optional): 'noise' (default) or 'blank'. 'blank' images will break u-inferforce drift correction (flat template).
% - 'DummySeed' (optional): RNG seed for dummy images (default: 42)
% - 'DummyNoiseMean' (optional): mean intensity for dummy noise images (default: 100)
% - 'DummyNoiseStd' (optional): std intensity for dummy noise images (default: 50)
%
% Output files created:
% - outMovieDataMatPath : contains variable "MD" (u-inferforce MovieData object)
% - <OutputDirectory>/displacementField/displField.mat : contains variable "displField" (struct array pos/vec)
% - DummyImageDir/*.tif : blank images defining MD.imSize_ and MD.nFrames_
%
% Notes:
% - This does NOT recreate raw bead images. It only creates a minimal MovieData to let u-inferforce consume a displacement field.
% - After creating movieData.mat, you can run u-inferforce ForceFieldCalculationProcess (Step 4/5) using this MovieData.
%
% Example:
%   easy_to_use_input_data_to_uinferforce_movieData( ...
%       'datasets/Easy-to-use-TFM-datasets/dotmatdata/input_data.mat', ...
%       'datasets/u-inferforce-master-datasets/Results/movieData.mat', ...
%       'PixelSize_um', 0.108, 'TimeInterval_s', 1.0, 'NumAperture', 1.40, ...
%       'Fluorophore','GFP','Excitation_nm',488,'Emission_nm',507,'Exposure_ms',50);
%

% Interactive mode: allow calling with no arguments.
if nargin < 1 || isempty(inputDataMatPath)
    if usejava('desktop')
        [f,p] = uigetfile('*.mat','Select Easy-to-use input_data.mat');
        if isequal(f,0), return; end
        inputDataMatPath = fullfile(p,f);
    else
        error('inputDataMatPath is required (GUI not available to prompt).');
    end
end
if nargin < 2 || isempty(outMovieDataMatPath)
    if usejava('desktop')
        defaultOutDir = fileparts(inputDataMatPath);
        if isempty(defaultOutDir), defaultOutDir = pwd; end
        defaultOut = fullfile(defaultOutDir,'movieData.mat');
        [f,p] = uiputfile('*.mat','Save u-inferforce movieData.mat as', defaultOut);
        if isequal(f,0), return; end
        outMovieDataMatPath = fullfile(p,f);
    else
        error('outMovieDataMatPath is required (GUI not available to prompt).');
    end
end

ip = inputParser;
ip.addRequired('inputDataMatPath', @ischar);
ip.addRequired('outMovieDataMatPath', @ischar);
ip.addParameter('PixelSize_um', [], @(x) isempty(x) || (isscalar(x) && isnumeric(x) && x > 0));
ip.addParameter('TimeInterval_s', [], @(x) isempty(x) || (isscalar(x) && isnumeric(x) && x > 0));
ip.addParameter('NumAperture', [], @(x) isempty(x) || (isscalar(x) && isnumeric(x) && x > 0));
ip.addParameter('CamBitdepth', 16, @(x) isscalar(x) && isnumeric(x) && x > 0);
ip.addParameter('Fluorophore', '', @ischar);
ip.addParameter('Excitation_nm', [], @(x) isempty(x) || (isscalar(x) && isnumeric(x) && x > 0));
ip.addParameter('Emission_nm', [], @(x) isempty(x) || (isscalar(x) && isnumeric(x) && x > 0));
ip.addParameter('Exposure_ms', [], @(x) isempty(x) || (isscalar(x) && isnumeric(x) && x > 0));
ip.addParameter('ImageSize_px', [], @(x) isempty(x) || (isnumeric(x) && numel(x) == 2));
ip.addParameter('DummyImageDir', '', @ischar);
ip.addParameter('OverwriteDummyImages', false, @(x) islogical(x) && isscalar(x));
ip.addParameter('DummyImageMode', 'noise', @(x) ischar(x) && ismember(lower(x), {'noise','blank'}));
ip.addParameter('DummySeed', 42, @(x) isscalar(x) && isnumeric(x));
ip.addParameter('DummyNoiseMean', 100, @(x) isscalar(x) && isnumeric(x));
ip.addParameter('DummyNoiseStd', 50, @(x) isscalar(x) && isnumeric(x) && x >= 0);
ip.parse(inputDataMatPath, outMovieDataMatPath, varargin{:});
opt = ip.Results;

% Make stable local copies of paths (some MATLAB environments can clear
% function workspaces after certain "clear" operations; avoid surprises).
inputPath = char(inputDataMatPath);
outPath = char(outMovieDataMatPath);

% If PixelSize_um wasn't provided, prompt the user.
if isempty(opt.PixelSize_um)
    if usejava('desktop')
        answ = inputdlg({'Pixel size (um/pixel):'}, 'Required parameter', 1, {'0.108'});
        if isempty(answ), return; end
        opt.PixelSize_um = str2double(answ{1});
    end
    assert(~isempty(opt.PixelSize_um) && isfinite(opt.PixelSize_um) && opt.PixelSize_um > 0, ...
        'PixelSize_um is required (um/pixel).');
end

% u-inferforce requires the beads channel PSF sigma for displacement/force processes.
% PSF sigma is computed from: numerical aperture, pixel size, emission wavelength.
% If NA/emission weren't provided, prompt the user in interactive mode.
if isempty(opt.NumAperture) && usejava('desktop')
    answ = inputdlg({'Numerical aperture (NA):'}, 'Required for u-inferforce (PSF sigma)', 1, {'1.40'});
    if isempty(answ), return; end
    opt.NumAperture = str2double(answ{1});
end
if isempty(opt.Emission_nm) && usejava('desktop')
    answ = inputdlg({'Emission wavelength (nm):'}, 'Required for u-inferforce (PSF sigma)', 1, {'507'});
    if isempty(answ), return; end
    opt.Emission_nm = str2double(answ{1});
end
assert(~isempty(opt.NumAperture) && isfinite(opt.NumAperture) && opt.NumAperture > 0, ...
    'NumAperture is required (e.g. 1.40) for u-inferforce PSF sigma.');
assert(~isempty(opt.Emission_nm) && isfinite(opt.Emission_nm) && opt.Emission_nm > 0, ...
    'Emission_nm is required (e.g. 507) for u-inferforce PSF sigma.');

% u-inferforce TFMPackage also requires a valid frame rate (time interval).
% If not provided, prompt in interactive mode.
if isempty(opt.TimeInterval_s) && usejava('desktop')
    answ = inputdlg({'Time interval (s) between frames:'}, 'Required for u-inferforce (frame rate)', 1, {'1.0'});
    if isempty(answ), return; end
    opt.TimeInterval_s = str2double(answ{1});
end
assert(~isempty(opt.TimeInterval_s) && isfinite(opt.TimeInterval_s) && opt.TimeInterval_s > 0, ...
    'TimeInterval_s is required (e.g. 1.0) for u-inferforce frame rate.');

% Put u-inferforce classes on path (and restore afterwards to avoid collisions).
origPath = path; %#ok<NASGU>
cleanupPath = onCleanup(@() path(origPath)); %#ok<NASGU>
thisFileDir = fileparts(mfilename('fullpath')); % .../datasets/tools
repoRoot = fileparts(fileparts(thisFileDir));   % .../tfm-algorithm-benchmark
uinferforceSoftwareDir = fullfile(repoRoot,'algorithms','matlab','u-inferforce-master','software');
assert(exist(uinferforceSoftwareDir,'dir') == 7, 'u-inferforce software dir not found: %s', uinferforceSoftwareDir);
addpath(genpath(uinferforceSoftwareDir), '-begin');
rehash;

% IMPORTANT: ensure MovieData objects are destroyed BEFORE restoring path.
% onCleanup executes in reverse creation order, so this runs first.
cleanupMD = onCleanup(@local_clear_objects); %#ok<NASGU>

% Load input_data
S = load(inputPath);
assert(isfield(S,'input_data'), 'Input MAT must contain struct variable ''input_data'': %s', inputPath);
assert(isfield(S.input_data,'displacement'), 'input_data.displacement missing in: %s', inputPath);
src = S.input_data.displacement;
assert(isstruct(src) && all(isfield(src,{'pos','vec'})), 'input_data.displacement must be struct array with pos/vec.');
T = numel(src);

% Normalize to displField (double)
displField(1,T) = struct('pos',[],'vec',[]); %#ok<NASGU,AGROW>
maxX = 1; maxY = 1;
for t = 1:T
    pos = double(src(t).pos);
    vec = double(src(t).vec);
    assert(size(pos,2) == 2, 'pos must be N×2');
    assert(size(vec,2) == 2, 'vec must be N×2');
    displField(t).pos = pos;
    displField(t).vec = vec;
    if ~isempty(pos)
        maxX = max(maxX, max(pos(:,1)));
        maxY = max(maxY, max(pos(:,2)));
    end
end

% Decide image size
if isempty(opt.ImageSize_px)
    margin = 10;
    width = max(1, ceil(maxX) + margin);
    height = max(1, ceil(maxY) + margin);
else
    height = int32(opt.ImageSize_px(1));
    width  = int32(opt.ImageSize_px(2));
    assert(height > 0 && width > 0, 'ImageSize_px must be positive.');
end

% Where to save movieData.mat and analysis outputs
outMDDir = fileparts(outPath);
if isempty(outMDDir), outMDDir = pwd; end
if exist(outMDDir,'dir') ~= 7
    mkdir(outMDDir);
end

% Dummy image folder
dummyDir = opt.DummyImageDir;
if isempty(dummyDir)
    dummyDir = fullfile(outMDDir, 'dummy_beads_images');
end
if exist(dummyDir,'dir') ~= 7
    mkdir(dummyDir);
end

% Create dummy images if needed
needWrite = opt.OverwriteDummyImages;
if ~needWrite
    % If folder doesn't have enough tifs, write them.
    tifList = dir(fullfile(dummyDir, '*.tif'));
    tifList2 = dir(fullfile(dummyDir, '*.tiff'));
    nHave = numel(tifList) + numel(tifList2);
    if nHave < T
        needWrite = true;
    end
end
if needWrite
    for t = 1:T
        fname = fullfile(dummyDir, sprintf('beads_%04d.tif', t));
        if strcmpi(opt.DummyImageMode,'blank')
            img = zeros(double(height), double(width), 'uint16');
        else
            % Non-flat dummy images to avoid failures in normxcorr2/checkIfFlat.
            rng(double(opt.DummySeed) + double(t), 'twister');
            mu = double(opt.DummyNoiseMean);
            sd = double(opt.DummyNoiseStd);
            x = mu + sd .* randn(double(height), double(width));
            x = max(0, min(65535, x));
            img = uint16(round(x));
        end
        imwrite(img, fname, 'tif');
    end
end

% Build Channel + MovieData
c = Channel(dummyDir);
c.name_ = 'beads';
if ~isempty(opt.Fluorophore), c.fluorophore_ = opt.Fluorophore; end
if ~isempty(opt.Excitation_nm), c.excitationWavelength_ = opt.Excitation_nm; end
if ~isempty(opt.Emission_nm), c.emissionWavelength_ = opt.Emission_nm; end
if ~isempty(opt.Exposure_ms), c.exposureTime_ = opt.Exposure_ms; end

outputDirectory = outMDDir; % keep analysis outputs next to movieData.mat by default
MD = MovieData(c, outputDirectory); %#ok<NASGU>
MD.movieDataPath_ = outMDDir;
[~,nm,ext] = fileparts(outPath);
MD.movieDataFileName_ = [nm ext];
MD.pixelSize_ = opt.PixelSize_um * 1000; % um -> nm
MD.timeInterval_ = opt.TimeInterval_s;
if ~isempty(opt.NumAperture), MD.numAperture_ = opt.NumAperture; end
MD.camBitdepth_ = opt.CamBitdepth;

% Create displacement process and point it to our displField.mat
dispOutDir = fullfile(outputDirectory, 'displacementField');
if exist(dispOutDir,'dir') ~= 7
    mkdir(dispOutDir);
end
displFieldPath = fullfile(dispOutDir, 'displField.mat');
save(displFieldPath, 'displField', '-v7.3');

funParams = DisplacementFieldCalculationProcess.getDefaultParams(MD, outputDirectory);
funParams.OutputDirectory = dispOutDir;
funParams.ChannelIndex = 1;
funParams.useGrid = false;
funParams.addNonLocMaxBeads = false;

proc = DisplacementFieldCalculationProcess(MD, outputDirectory, funParams);
outFiles = cell(2,1);
outFiles{1,1} = displFieldPath;
outFiles{2,1} = fullfile(dispOutDir, 'dMap.mat'); % optional, may not exist
proc.setOutFilePaths(outFiles);
MD.addProcess(proc);

% Run sanityCheck (sets imSize_/nFrames_ from dummy images + saves movieData.mat)
MD.sanityCheck();

fprintf('Created u-inferforce MovieData at: %s\n', outPath);
fprintf('Dummy images dir: %s\n', dummyDir);
fprintf('Displacement field: %s\n', displFieldPath);

end

function local_clear_objects()
% Clear handle objects before path restoration to avoid warnings when MATLAB
% tries to resolve class methods during destruction.
try %#ok<TRYNC>
    MD = []; %#ok<NASGU>
    proc = []; %#ok<NASGU>
    c = []; %#ok<NASGU>
end
end

