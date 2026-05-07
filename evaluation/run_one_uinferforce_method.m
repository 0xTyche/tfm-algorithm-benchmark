function run_one_uinferforce_method(movieDataPath, outDir, methodName, youngKPa, regParam)
%RUN_ONE_UINFERFORCE_METHOD Run one force inversion method and save CSV.
if nargin < 1 || isempty(movieDataPath), movieDataPath = fullfile('datasets','real_data','result','movieData.mat'); end
if nargin < 2 || isempty(outDir), outDir = fullfile('datasets','real_data','result','six_method_results','FTTC'); end
if nargin < 3 || isempty(methodName), methodName = 'FTTC'; end
if nargin < 4 || isempty(youngKPa), youngKPa = 60.0; end
if nargin < 5 || isempty(regParam), regParam = 2e-6; end

repoRoot = fileparts(fileparts(mfilename('fullpath')));
uinferforceSoftwareDir = fullfile(repoRoot, 'algorithms', 'matlab', 'u-inferforce-master', 'software');
addpath(genpath(uinferforceSoftwareDir), '-begin');
rehash;

movieDataPath = local_to_abs(movieDataPath, repoRoot);
outDir = local_to_abs(outDir, repoRoot);
if exist(outDir, 'dir') ~= 7
    mkdir(outDir);
end

S = load(movieDataPath);
MD = S.MD;

params = ForceFieldCalculationProcess.getDefaultParams(MD, outDir);
params.OutputDirectory = outDir;
params.YoungModulus = youngKPa * 1000;
params.PoissonRatio = 0.5;
params.regParam = regParam;
params.useLcurve = false;
params.method = 'FastBEM';
params.solMethodBEM = methodName;
params.meshPtsFwdSol = 1024;
params.divideConquer = 1;
params.lastToFirst = false;

if strcmpi(methodName, 'FTTC')
    params.method = 'FTTC';
end

calculateMovieForceField(MD, params);

ffPath = fullfile(outDir, 'forceField.mat');
ff = load(ffPath, 'forceField');
cur = ff.forceField(1);
pos = double(cur.pos);
vec = double(cur.vec);
mag = hypot(vec(:,1), vec(:,2));
writematrix([pos vec mag], fullfile(outDir, 'traction_frame1_xy_tx_ty_mag.csv'));

fprintf('Done method %s -> %s\n', methodName, outDir);
end

function p = local_to_abs(p, repoRoot)
if ~(startsWith(p, filesep) || ~isempty(regexp(p, '^[A-Za-z]:', 'once')))
    p = fullfile(repoRoot, p);
end
p = char(java.io.File(p).getCanonicalPath());
end
