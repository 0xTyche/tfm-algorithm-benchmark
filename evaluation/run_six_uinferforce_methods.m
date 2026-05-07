function run_six_uinferforce_methods(varargin)
%RUN_SIX_UINFERFORCE_METHODS Batch-run six u-inferforce solvers on one MovieData.
%
% This script runs six FastBEM solver variants on the same displacement
% field and stores each method output in a separate folder.
%
% Usage (MATLAB):
%   run_six_uinferforce_methods( ...
%       'MovieDataPath', 'datasets/real_data/result/movieData.mat', ...
%       'OutputRoot', 'datasets/real_data/result/six_method_results', ...
%       'YoungModulusKPa', 60.0, ...
%       'RegParam', 2e-6);
%
% Outputs (for each method):
%   <OutputRoot>/<Method>/forceField.mat
%   <OutputRoot>/<Method>/tractionMaps.mat
%   <OutputRoot>/<Method>/traction_frame1_xy_tx_ty_mag.csv
%
% Global summary:
%   <OutputRoot>/summary.json

ip = inputParser;
ip.addParameter('MovieDataPath', fullfile('datasets', 'real_data', 'result', 'movieData.mat'), @ischar);
ip.addParameter('OutputRoot', fullfile('datasets', 'real_data', 'result', 'six_method_results'), @ischar);
ip.addParameter('YoungModulusKPa', 60.0, @(x) isnumeric(x) && isscalar(x) && x > 0);
ip.addParameter('RegParam', 2e-6, @(x) isnumeric(x) && isscalar(x) && x > 0);
ip.parse(varargin{:});
opt = ip.Results;

repoRoot = fileparts(fileparts(mfilename('fullpath')));
uinferforceSoftwareDir = fullfile(repoRoot, 'algorithms', 'matlab', 'u-inferforce-master', 'software');
assert(exist(uinferforceSoftwareDir, 'dir') == 7, 'u-inferforce software dir not found: %s', uinferforceSoftwareDir);
addpath(genpath(uinferforceSoftwareDir), '-begin');
rehash;

movieDataPath = local_to_abs(opt.MovieDataPath, repoRoot);
outputRoot = local_to_abs(opt.OutputRoot, repoRoot);
if exist(outputRoot, 'dir') ~= 7
    mkdir(outputRoot);
end

S = load(movieDataPath);
MD = [];
if isfield(S, 'MD')
    MD = S.MD;
else
    fns = fieldnames(S);
    for i = 1:numel(fns)
        if isa(S.(fns{i}), 'MovieData')
            MD = S.(fns{i});
            break;
        end
    end
end
assert(~isempty(MD) && isa(MD, 'MovieData'), 'Failed to load MovieData object from: %s', movieDataPath);

% Six traction inversion variants for practical batch execution.
% Note: 1NormRegLaplacian can fail on some datasets due a toolbox bug, so
% we use FTTC as a stable sixth method.
methods = {'QR', 'svd', 'backslash', '1NormReg', 'LaplacianReg', 'FTTC'};
summary = struct();
summary.movieDataPath = movieDataPath;
summary.outputRoot = outputRoot;
summary.youngModulusKPa = opt.YoungModulusKPa;
summary.regParam = opt.RegParam;
summary.methods = methods;
summary.runs = cell(1, numel(methods));

for i = 1:numel(methods)
    methodName = methods{i};
    outDir = fullfile(outputRoot, methodName);
    if exist(outDir, 'dir') ~= 7
        mkdir(outDir);
    end

    fprintf('[%d/%d] Running method: %s\n', i, numel(methods), methodName);

    params = ForceFieldCalculationProcess.getDefaultParams(MD, outDir);
    params.OutputDirectory = outDir;
    params.YoungModulus = opt.YoungModulusKPa * 1000; % kPa -> Pa
    params.PoissonRatio = 0.5;
    params.method = 'FastBEM';
    params.solMethodBEM = methodName;
    params.regParam = opt.RegParam;
    params.meshPtsFwdSol = 1024;
    params.useLcurve = false;
    params.divideConquer = 1;
    params.lastToFirst = false;
    params.saveBEMparams = true;
    if strcmpi(methodName, 'FTTC')
        params.method = 'FTTC';
        params.useLcurve = false;
    end

    calculateMovieForceField(MD, params);

    ffPath = fullfile(outDir, 'forceField.mat');
    assert(exist(ffPath, 'file') == 2, 'forceField.mat not found for method: %s', methodName);
    ff = load(ffPath, 'forceField');
    assert(isfield(ff, 'forceField') && ~isempty(ff.forceField), 'Invalid forceField in: %s', ffPath);

    frameId = 1;
    cur = ff.forceField(frameId);
    pos = double(cur.pos);
    vec = double(cur.vec);
    mag = hypot(vec(:, 1), vec(:, 2));

    outCsv = fullfile(outDir, sprintf('traction_frame%d_xy_tx_ty_mag.csv', frameId));
    writematrix([pos vec mag], outCsv);

    runInfo = struct();
    runInfo.method = methodName;
    runInfo.outputDirectory = outDir;
    runInfo.forceFieldMat = ffPath;
    runInfo.tractionMapsMat = fullfile(outDir, 'tractionMaps.mat');
    runInfo.frame = frameId;
    runInfo.numVectors = size(pos, 1);
    runInfo.meanTractionPa = mean(mag, 'omitnan');
    runInfo.meanTractionKPa = runInfo.meanTractionPa / 1000;
    runInfo.csv = outCsv;
    summary.runs{i} = runInfo;

    fprintf('  Done %s | N=%d | mean traction=%.4f kPa\n', methodName, runInfo.numVectors, runInfo.meanTractionKPa);
end

summaryPath = fullfile(outputRoot, 'summary.json');
fid = fopen(summaryPath, 'w');
assert(fid > 0, 'Failed to write summary json: %s', summaryPath);
fprintf(fid, '%s\n', jsonencode(summary, 'PrettyPrint', true));
fclose(fid);

fprintf('\nAll six methods completed.\nSummary: %s\n', summaryPath);

end

function p = local_to_abs(p, repoRoot)
if isempty(p)
    p = repoRoot;
    return;
end
if ~isfolder(fileparts(p)) && ~contains(p, filesep)
    p = fullfile(repoRoot, p);
elseif ~(startsWith(p, filesep) || ~isempty(regexp(p, '^[A-Za-z]:', 'once')))
    p = fullfile(repoRoot, p);
end
p = char(java.io.File(p).getCanonicalPath());
end
