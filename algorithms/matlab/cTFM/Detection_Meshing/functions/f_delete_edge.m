%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% f_delete_edge is called by the cTFM mesh generator        %
%                                                           %
% This function lets the user delete a manually added       %
% edge. Other edges are not affected.                       %
%                                                           %
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

function manual_conn = f_delete_edge(handles)
%show manual connections
%f_axis_control(handles,'manual_conn')
%select manual connection to delete
[x,y] = ginput(2);

IDX = zeros(2,1);
D = zeros(2,1);
for i = 1:2
    [IDX(i),~] = knnsearch(handles.var.KDTree.X,[x(i),y(i)]);
end

%find IDX in the manual connections
manual_conn = handles.var.manual_conn;
tmp = sum(ismember(manual_conn,IDX),2)==2;
if isempty(tmp)
    %invalid selection for removal made
else
    manual_conn(tmp,:) = [];
end

hold on
x_m = handles.var.xcoords(IDX);
y_m = handles.var.ycoords(IDX);
scatter(mean(x_m),mean(y_m),'rx')
line(x_m,y_m,'Color','k')
hold off