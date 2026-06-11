%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% f_Aloeq is called by the cTFM mesh generator              %
%                                                           %
% This function is called during the meshing procedure. It  %
% generates the matrix Aloeq for the optimization during    %
% the process of finding the image border.                  %
%                                                           %
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

function [Aloeq] = f_Aloeq(intersect)
    A = intersect.intAdjacencyMatrix;
    Delta = intersect.intNormalizedDistance1To2;

    N = length(A);
    M = sum(sum(A))/2;
    Aloeq = zeros(M,N);
    k = 1;
    for i=1:N
        for j=i:N
            if A(i,j) == 1 && Delta(i,j) > 0.000001 && Delta(i,j) < 0.999999
                Aloeq(k,[i,j]) = 1;
                k = k+1;
            end
        end
    end
    Aloeq = sparse(Aloeq);
end