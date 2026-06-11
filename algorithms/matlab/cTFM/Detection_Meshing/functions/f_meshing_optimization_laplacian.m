%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% f_meshing_optimization_laplacian is called by the         %
% cTFM mesh generator                                       %
%                                                           %
% This function is called during the meshing procedure for  %
% the optimization of the difficult to mesh regions. It     %
% includes multiple sections. First the borders of the un-  %
% meshed clusters are checked as well as the number of      %
% internal vertices. If the clustur is feasible, then a     %
% perfect mesh is generated for the cluster and fitted to   %
% the cluster boundary. Next the matrices for the           %
% optimization are created (the laplacian and the           %
% constraints). After that f_gurobi is called to minimize   %
% the overall displacements of each internal vertex to fit  %
% the vertices of the perfect grid. This mapping is then    %
% used to generate the connectivity of grid of the cluster. %
%                                                           %
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

function [edges,info_output,valid]=f_meshing_optimization_laplacian(I,info_output,groups,clusters,missing_entries,xcoords,ycoords,hex_index);
    %% grid reconstruction
    cluster_boundary = clusters.edges{I};
    in_cluster = clusters.all_incluster{I};
    
    V_0 = [cluster_boundary';in_cluster];
    V_0_coords = [xcoords(V_0),ycoords(V_0)];
    iNrCE = length(cluster_boundary); %number of vertices in cluster edges
    iNrVI = length(in_cluster); %number of inner vertices
    
    manually_connected = unique(groups.manual_conn);
    
    if isempty(manually_connected) || sum(ismember(cluster_boundary,manually_connected))==0

        for i = 1:length(cluster_boundary)
            nr_inward_conns(i) = sum(ismember(in_cluster,hex_index(cluster_boundary(i),:))); %find number of connections going into the cluster
            %nr_conns(i) = sum(logical(hex_index(cluster_boundary(i),:))); %find number of connections going into the cluster

            neigh(i) = 6 - nr_inward_conns(i);
        end 
    else
        bins = [0,30,90,150,210,270,330,360];
        for i = 1:length(cluster_boundary)
            if i == 1
                P0 = [xcoords(cluster_boundary(end)),ycoords(cluster_boundary(end))];
                P2 = [xcoords(cluster_boundary(i+1)),ycoords(cluster_boundary(i+1))];
            elseif i == length(cluster_boundary)
                P0 = [xcoords(cluster_boundary(i-1)),ycoords(cluster_boundary(i-1))];
                P2 = [xcoords(cluster_boundary(1)),ycoords(cluster_boundary(1))];
            else
                P0 = [xcoords(cluster_boundary(i-1)),ycoords(cluster_boundary(i-1))];
                P2 = [xcoords(cluster_boundary(i+1)),ycoords(cluster_boundary(i+1))];
            end
            P1 = [xcoords(cluster_boundary(i)),ycoords(cluster_boundary(i))];

            v1 = P0 - P1;
            v2 = P2 - P1;

            ang = atan2(v1(1)*v2(2)-v2(1)*v1(2),v1(1)*v2(1)+v1(2)*v2(2));
            Angle = mod(-180/pi * ang, 360);

            ind = discretize(Angle, bins);
            neigh(i) = ind;
        end
    end
    V_Io = [xcoords(in_cluster) ycoords(in_cluster) zeros(iNrVI,1)];
    V_boundary = [xcoords(cluster_boundary) ycoords(cluster_boundary) zeros(iNrCE,1)];

    % Test the validity of the neigh
    [valid] = is_neigh_valid_mex(neigh);
    
    % If valid mesh and plot it
    if valid == 1
        % Call the meshing function
        [V,F] = grid_meshing_mex(V_boundary,V_Io,neigh);

        % Plot the mesh
%         figure
%         trimesh(F,V(:,1),V(:,2),'Color','b');
%         axis vis3d;
%         set(gca,'YDir','reverse');
    else
        edges = [];
        info_output.description = [];
        return
    end
    
    %remove vertices that don't belong to polygon (e.g. internal holes)
    [Ind_in_cluster] = inpolygon(V(:,1),V(:,2),...
            xcoords(cluster_boundary),ycoords(cluster_boundary));
    V = V(Ind_in_cluster,:);
    
    Ind_remove = find(Ind_in_cluster==0);
    for i = 1:length(Ind_remove)
        [rows,~] = find(ismember(F,Ind_remove(i)));
        F(rows,:) = [];
        F(F>Ind_remove(i)) = F(F>Ind_remove(i))-1;
        Ind_remove = Ind_remove - 1; 
    end
    
    %% generate discrete uniform laplacian for inner vertices of perfect mesh
    iNrT = length(F); %number of triangles
    iNrV = length(V); %number of vertices
    
    % Build sparse adjacency matrix and Laplacian without allocating a full dense matrix.
    % Each triangle contributes 6 directed edges (one per ordered vertex pair).
    ii = [F(:,1); F(:,1); F(:,2); F(:,2); F(:,3); F(:,3)];
    jj = [F(:,2); F(:,3); F(:,1); F(:,3); F(:,1); F(:,2)];
    A = spones(sparse(ii, jj, 1, iNrV, iNrV));
    L = spdiags(sum(A,2), 0, iNrV, iNrV) - A;
    
    %reduce to inner vertices
%     L_I = sparse(L(iNrCE+1:end,iNrCE+1:end));
%     V_Ip = V(iNrCE+1:end,:);

    %% Q for optimization
    K = 15;
    if iNrV < K;
        K = iNrV;
    end
    KDTree_iV = createns(V_0_coords());
    
    % K Nearest neighbors only
    Q1 = [];
    Vx = [];
    Vy = [];
    IDX = zeros(K,iNrV);
    Q2 = 1:K*iNrV;
    for i = 1:iNrV
        K_closest = knnsearch(KDTree_iV,[V(i,1),V(i,2)],'k',K);
        Q1 = [Q1,repmat(i,1,K)];
        Vx = [Vx;V_0_coords(K_closest,1)];
        Vy = [Vy;V_0_coords(K_closest,2)];
        IDX(:,i) = K_closest;
    end
    
    VK_x = sparse(Q1,Q2,Vx);
    VK_y = sparse(Q1,Q2,Vy);
    
    Q = VK_x'*(L')*L*VK_x + VK_y'*(L')*L*VK_y; 
    
    
    %% Generating constraints
    % Aeq x = beq
    % constraint 1: only one entry per row of M
    %Aeq1 = kron(speye(iNrV),ones(1,iNrV)); % <--- use this without proximity constraint
    Aeq1 = kron(speye(iNrV),ones(1,K)); % <--- use this with proximity constraint K
    beq1 = ones(iNrV,1);
    
    %constraint 2: only one entry per column of M
    %Aeq2 = kron(ones(1,iNrV),speye(iNrV)); % <--- use this without proximity constraint
    Aeq2 = zeros(iNrV,K*iNrV);
    for i = 1:iNrV
        ind_V = IDX == i;
        ind_V = ind_V(:);
        Aeq2(i,:) = ind_V;
    end
    beq2 = ones(iNrV,1);
    
    %constraint 3: vertices on cluster edge remain unmoved
    %first entries of V equal to cluster_boundary i.e. V(1:iNrCE,1) ==
    %xcoords(cluster_boundary)
%     Aeq3 = zeros(iNrCE,iNrV^2); % <--- use this without proximity constraint
    Aeq3 = zeros(iNrCE,K*iNrV); % <--- use this with proximity constraint K
    for i = 1:iNrCE
%         Aeq3(i,i+(i-1)*iNrV) = 1; % <--- use this without proximity constraint
        Aeq3(i,1+(i-1)*K) = 1; % <--- use this with proximity constraint K
    end
    Aeq3 = sparse(Aeq3);
    beq3 = ones(iNrCE,1);
    
    %constraint 4: proximity - only consider K closest vertices as options
%     Aeq4 = zeros(iNrV,iNrV^2);
%     for i = 1:iNrV
%         IDX = knnsearch(KDTree_iV,[V(i,1),V(i,2)],'k',K);
%         Aeq4(i,(i-1)*iNrV+IDX) = 1;
%     end
%     Aeq4 = sparse(Aeq4);
%     beq4 = ones(iNrV,1);
    
    Aeq = [Aeq1;Aeq2;Aeq3];
    beq = [beq1;beq2;beq3];    
    
    
    %% Gurobi
    iVars = K*iNrV;
    clear model result; 
    model.A = Aeq;
    model.obj = ones(1,iVars);
    model.rhs = beq;
    model.sense = '=';
    model.modelsense = 'min';
    model.vtype = 'B';
    
    model.Q = Q;


%     model.lb = zeros(iVars,1);
%     model.ub = ones(iVars,1);
    
    clear params;
    params.outputflag = 1; %set to 1 to see output in command window 
    params.resultfile = '';
    %params.IterationLimit = 1000000;
    params.timelimit = 3600;
    result = gurobi(model, params);
    
    if isfield(result, 'x') == 0
        edges = [];
        info_output.description = [];
        return
    end
    
    %% Mapping
    mat = logical(round(vec2mat(result.x,K)));
    
    assert(sum(sum(mat,2)~=1)==0) %rows only contain one entry
    
    V_mapping = zeros(iNrV,1);
    for i = 1:iNrV
        ind = IDX(mat(i,:),i);
        V_mapping(i) = ind;
    end
    T = V_0(V_mapping(F));
    
    %Plot the mesh
    hold on
    trimesh(T,xcoords,ycoords,'Color','w');
    
    %% Edges
    
    edges = zeros(3*iNrV,2);
    for i = 1:iNrT
        temp = sort(T(i,:));
        edges(3*(i-1)+1,:) = [temp(1),temp(2)];
        edges(3*(i-1)+2,:) = [temp(1),temp(3)];
        edges(3*(i-1)+3,:) = [temp(2),temp(3)];
    end
    edges = unique(edges,'rows');
    
    
    %% TODO: Handling 
%     if strcmp(result.status,'INFEASIBLE')
%                 disp(['Gurobi did not find a solution for cluster ',num2str(i)])
%     elseif strcmp(result.status,'OPTIMAL')
%             info_output.description = [info_output.discription,'Optimal solution ',...
%                 'without intersection for cluster ',num2str(i),...
%                 ' was not found after the maximum iterations.\n',...
%                 'Consider making manual connections and using stiffer substrates\n\n']; 
%             info_output.type = 1;
%         end
%     end
    info_output.description = ['Laplacian optimization...'];
    info_output.type = 0;
    %% Control
    % v = rand(3,1);
    % % M = rand(3,3);
    % % L = rand(3,3);
    % 
    % v = [1;2;3];
    % M = [3,4,5;6,7,8;9,10,11];
    % L = [1.5,2.5,3.5;4.5,5.5,6.5;0.5,3.5,7.5];
    % 
    % L = L + L';
    % 
    % 
    % disp('Correct:')
    % disp(v'*M'*(L')*L*M*v)
    % 
    % 
    % disp('Unroll:')
    % 
    % s = 0;
    % 
    % for a=1:3
    %     for b=1:3
    %         for c=1:3
    %             for d=1:3
    %                 for e=1:3
    %                     s = s + v(a)*M(b,a)*L(c,b)*L(c,d)*M(d,e)*v(e);
    %                 end
    %             end
    %         end
    %     end
    % end
    % disp(s)
    % 
    % disp('Kronecker:')
    % 
    % m = reshape(M',9,1);
    % 
    % VK = kron(eye(3),v');
    % 
    % temp = L*VK*m;
    % 
    % disp(temp' * temp)
