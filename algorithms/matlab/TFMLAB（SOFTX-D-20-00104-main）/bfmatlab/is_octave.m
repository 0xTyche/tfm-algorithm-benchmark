function tf = is_octave()
%IS_OCTAVE Return true if running in GNU Octave, false if running in MATLAB.
%
% TFMLAB uses OME Bio-Formats' bfmatlab helpers which sometimes branch for
% Octave vs MATLAB. This project targets MATLAB, so we provide this helper
% to avoid bfmatlab functions failing when the upstream helper is missing.

tf = (exist('OCTAVE_VERSION', 'builtin') ~= 0);
end

