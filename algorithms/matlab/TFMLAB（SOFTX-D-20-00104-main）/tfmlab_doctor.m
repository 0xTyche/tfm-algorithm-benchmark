function tfmlab_doctor()
%TFMLAB_DOCTOR Quick environment check for TFMLAB (beginner-friendly).
%
% Run this from the TFMLAB project root:
%   >> tfmlab_doctor
%
% It will:
% - Add required TFMLAB folders to MATLAB path (including bfmatlab)
% - Check optional dependencies and print clear next-step instructions
%
% NOTE: This does not modify your system permanently (no installs).

clc;
fprintf('TFMLAB doctor (environment check)\n');
fprintf('--------------------------------\n');

root = fileparts(mfilename('fullpath'));
fprintf('Project root: %s\n\n', root);

% Add TFMLAB folders to path (session-only)
addpath(genpath(root));
addpath(genpath(fullfile(root, 'bfmatlab'))); % ensure bfGetReader/bfopen are visible

% 1) MATLAB version
try
    v = ver('MATLAB');
    fprintf('[OK] MATLAB detected: %s\n', v.Version);
catch
    fprintf('[WARN] Could not detect MATLAB version (unexpected).\n');
end

% 2) Sample data
sampleLif = fullfile(root, 'data', 'PaperData.lif');
if exist(sampleLif, 'file') == 2
    info = dir(sampleLif);
    fprintf('[OK] Sample data found: data/PaperData.lif (%.1f MB)\n', info.bytes/1024/1024);
else
    fprintf('[WARN] Sample data NOT found at: data/PaperData.lif\n');
end

% 3) Elastix binaries
elx = fullfile(root, 'elastixLib', 'elastix.exe');
trx = fullfile(root, 'elastixLib', 'transformix.exe');
if exist(elx, 'file') == 2 && exist(trx, 'file') == 2
    fprintf('[OK] elastix binaries found under elastixLib/\n');
else
    fprintf('[WARN] elastix binaries missing under elastixLib/ (needed for displacement calculation)\n');
end

% 4) DIPImage (optional but commonly needed)
% DIPImage usually provides the class "dip_image" and a startup file "dipstart.m".
hasDip = (exist('dip_image', 'class') == 8) || (exist('dipstart', 'file') == 2);
if hasDip
    fprintf('[OK] DIPImage appears to be available.\n');
else
    fprintf('[WARN] DIPImage not detected. TFMLAB image processing steps may fail.\n');
    fprintf('       Install DIPImage and add it to MATLAB path, then run dipstart.\n');
end

% 5) Bio-Formats jar (required to read .lif via bfGetReader)
jarPath = fullfile(root, 'bfmatlab', 'bioformats_package.jar');
if exist(jarPath, 'file') == 2
    fprintf('[OK] Bio-Formats jar found: bfmatlab/bioformats_package.jar\n');
else
    fprintf('[WARN] Bio-Formats jar NOT found at: bfmatlab/bioformats_package.jar\n');
    fprintf('       Without it, reading .lif will fail.\n');
end

% Try to validate Bio-Formats Java classpath (show diagnostics if it fails)
try
    bfCheckJavaMemory(1024); % warn only; does not error
catch
    % ignore
end

if exist(jarPath, 'file') == 2
    fprintf('      Bio-Formats jar full path: %s\n', jarPath);
    % Attempt to add to *dynamic* Java classpath for this session
    try
        javaaddpath(jarPath);
    catch ME
        fprintf('[WARN] javaaddpath failed:\n%s\n', getReport(ME,'extended','hyperlinks','off'));
    end
    try
        dyn = javaclasspath('-dynamic');
        inDyn = any(strcmpi(dyn, jarPath));
        fprintf('      In dynamic Java classpath: %d\n', inDyn);
    catch
        fprintf('[WARN] Could not read dynamic Java classpath.\n');
    end
end

% Direct class instantiation test (most reliable)
try
    javaObject('loci.formats.in.FakeReader');
    fprintf('[OK] Bio-Formats Java classes are loadable (loci.formats.*)\n');
catch ME
    fprintf('[WARN] Bio-Formats classes NOT loadable in this MATLAB session.\n');
    fprintf('       Error detail:\n%s\n', getReport(ME,'extended','hyperlinks','off'));
end

% bfmatlab helper check (secondary)
try
    [ok, version] = bfCheckJavaPath(true);
    if ok
        fprintf('[OK] bfCheckJavaPath(true) reports working (version: %s)\n', version);
    else
        fprintf('[WARN] bfCheckJavaPath(true) still reports NOT working.\n');
    end
catch ME
    fprintf('[WARN] bfCheckJavaPath(true) threw an error:\n%s\n', ME.message);
end

fprintf('\nNext steps (typical):\n');
fprintf('1) Run: main.m\n');
fprintf('2) In the first GUI (Input data), select your PaperData.lif and enable conversion to TIFF if prompted.\n');
fprintf('3) If you hit an error about Bio-Formats/JAR, fix bfmatlab/bioformats_package.jar first.\n');
fprintf('\nDone.\n');
end

