%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% f_gurobi is called by the cTFM mesh generator             %
%                                                           %
% This function calls the Gurobi API. The optimizer solves  %
% for x'*Q*x + f x = b with constraints Aeq*x = beq.        %
% Iteration and a timelimit may be set as parameter, but    %
% should be void to assure optimal result.                  %
%                                                           %
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

function result = f_gurobi(Aloeq,Aeq,beq,vertex_length)
%gurobi optimizer
iVars = size(Aeq,2);

try
    clear model result; 
    model.A = Aeq;
    model.obj = 0.01*vertex_length;%zeros(1,iVars);%ones(1,iVars);
    model.rhs = beq;
    model.sense = '=';
    model.modelsense = 'min';
    model.vtype = 'B';
    
    model.Q = Aloeq'*Aloeq;

%     model.lb = zeros(iVars,1);
%     model.ub = ones(iVars,1);
    
    clear params;
    params.outputflag = 1; %set to 1 to see output in command window 
    params.resultfile = '';
%     params.IterationLimit = 200000;
    params.timelimit = 300;
    result = gurobi(model, params);
    
    %check if crossings occur
    tmp = Aloeq * result.x;
    if isempty(find(tmp==2,1))
        result.crossing = 0;
    else
        result.crossing = 1;
    end
%     for v=1:length(names)
%         fprintf('%s %d\n', names{v}, result.x(v));
%     end
% 
%     fprintf('Obj: %e\n', result.objval);

catch gurobiError
    fprintf('Error reported:\n');
    disp(gurobiError)
end