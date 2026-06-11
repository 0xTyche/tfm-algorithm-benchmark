function varargout = cTFM_meshing(varargin)
% CTFM_MESHING MATLAB code for cTFM_meshing.fig
%      CTFM_MESHING, by itself, creates a new CTFM_MESHING or raises the existing
%      singleton*.
%
%      H = CTFM_MESHING returns the handle to a new CTFM_MESHING or the handle to
%      the existing singleton*.
%
%      CTFM_MESHING('CALLBACK',hObject,eventData,handles,...) calls the local
%      function named CALLBACK in CTFM_MESHING.M with the given input arguments.
%
%      CTFM_MESHING('Property','Value',...) creates a new CTFM_MESHING or raises the
%      existing singleton*.  Starting from the left, property value pairs are
%      applied to the GUI before cTFM_meshing_OpeningFcn gets called.  An
%      unrecognized property name or invalid value makes property application
%      stop.  All inputs are passed to cTFM_meshing_OpeningFcn via varargin.
%
%      *See GUI Options on GUIDE's Tools menu.  Choose "GUI allows only one
%      instance to run (singleton)".
%
% See also: GUIDE, GUIDATA, GUIHANDLES

% Edit the above text to modify the response to help cTFM_meshing

% Last Modified by GUIDE v2.5 20-Feb-2016 10:56:43

% Begin initialization code - DO NOT EDIT
gui_Singleton = 1;
gui_State = struct('gui_Name',       mfilename, ...
                   'gui_Singleton',  gui_Singleton, ...
                   'gui_OpeningFcn', @cTFM_meshing_OpeningFcn, ...
                   'gui_OutputFcn',  @cTFM_meshing_OutputFcn, ...
                   'gui_LayoutFcn',  [] , ...
                   'gui_Callback',   []);
if nargin && ischar(varargin{1})
    gui_State.gui_Callback = str2func(varargin{1});
end

if nargout
    [varargout{1:nargout}] = gui_mainfcn(gui_State, varargin{:});
else
    gui_mainfcn(gui_State, varargin{:});
end
% End initialization code - DO NOT EDIT


% --- Executes just before cTFM_meshing is made visible.
function cTFM_meshing_OpeningFcn(hObject, eventdata, handles, varargin)
% This function has no output args, see OutputFcn.
% hObject    handle to figure
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)
% varargin   command line arguments to cTFM_meshing (see VARARGIN)

% Choose default command line output for cTFM_meshing
handles.output = hObject;

%=====================================================================
% Startup Code that runs at start up ---------------------------------
    % Clear old stuff from console.
    clear handles.var
	clc;
	fprintf(1, 'Starting TFM GUI...\n');
	
	% Change the current folder to the folder of this m-file.
	% (The line of code below is from Brett Shoelson of The Mathworks.)
	cd(fileparts(which(mfilename)));

    % Add the path for the needed functions
    addpath('functions');
    
	% MATLAB QUIRK: Need to clear out any global variables you use anywhere
	% otherwise it will remember their prior values from a prior running of the macro.
    clear global;

	handles.macroFolder = cd;
	set(handles.figureMainWindow, 'Visible', 'off');

    % Load up the initial values from the mat file.
	strIniFile = fullfile(handles.macroFolder, 'cTFM_settings.mat');
	if exist(strIniFile, 'file')
		% Pull out values and stuff them in structure initialValues.
		initialValues = load(strIniFile);
		% Assign the image folder from the last_used_dir field of the
		% structure.
	    handles.var.ImageFolder = initialValues.last_used_dir;
	end
    
	% If the image folder does not exist, but the imdemos folder exists, then point them to that.
	if exist(handles.var.ImageFolder, 'dir') == 0
		% Folder stored in the mat file does not exist.  Try the imdemos folder instead.
		imdemosFolder = fullfile(matlabroot, '\toolbox\images\imdemos');
		if exist(imdemosFolder, 'dir') == 0
			% imdemos folder exists.  Use it.
			handles.var.ImageFolder = imdemosFolder;
		else
			% imdemos folder does not exist.  Use current folder.
			handles.var.ImageFolder = cd;
		end
	end
	% handles.var.ImageFolder will be a valid, existing folder by the time you get here.
	if exist(strIniFile, 'file')
		% If the mat file is not there, save current folder out in our mat file.
		% Save the image folder in our ini file.
		last_used_dir = handles.var.ImageFolder;
		save(strIniFile, 'last_used_dir');
	end
    set(handles.ctfm_txtFolder, 'string', handles.var.ImageFolder);
	
    %uiwait(msgbox(handles.var.ImageFolder));
    % Load list of images in the image folder.
    handles = LoadImageList(handles);
	% Select none of the items in the listbox.
	set(handles.ctfm_lstImageList, 'value', []);

	% Load a splash image.
    %axes(handles.axes_image);
	fullSplashImageName = fullfile(handles.macroFolder, '/splash.png');
	
	if exist(fullSplashImageName, 'file')
		% Display splash image.
		imgOriginal = imread(fullSplashImageName);
	else
		% Display something
		imgOriginal = peaks(300);
	end
    % Display image array in a window on the user interface.
	% Display in axes, storing handle of image for later quirk workaround.
	hold off;	% IMPORTANT NOTE: hold needs to be off in order for the "fit" feature to work correctly.
    axesChildHandle = imshow(imgOriginal, 'InitialMagnification', 'fit', 'parent', handles.axes_image);
	imageFolder = handles.var.ImageFolder;
	h = axesChildHandle;
	setappdata(h, 'imageFolder', imageFolder);
		
	% !!!! QUIRK workaround.!!!!
	% Make it so that if they click in the image axes, it will execute a
	% button down callback called "axes_image_ButtonDownFcn".
	% Now it won't  -- unless you do this quirk workaround.
	% Double click on the dialog box's (main figure's) background to bring up the property inspector.
	% Change both the WindowButtonDownFcn and ButtonDownFcn properties so that they are blank.
	% Also set the main figure's HitTest to off.  Then, make sure you already have the handle to the
	% image living in the axes by getting it from an imshow.  Then do this:
	set(axesChildHandle, 'ButtonDownFcn', @axes_image_ButtonDownFcn);
	% Put everything you want to do when they click the image into the function axes_image_ButtonDownFcn()
	% !!!! End QUIRK workaround.!!!!

    % Disable all buttons from processing before image is loaded
    enable_mesh_field(handles,'off')
    f_disp_control(handles,'nodes3D','off',0)
    
	fprintf(1, 'Done with initializing TFM Lab.\n');

	% Update handles structure
    guidata(hObject, handles);
    set(gcf,'Pointer','arrow');
    drawnow;
% --- End of My Startup Code --------------------------------------------------
%=====================================================================


% Update handles structure
guidata(hObject, handles);

% UIWAIT makes cTFM_meshing wait for user response (see UIRESUME)
% uiwait(handles.figureMainWindow);


% --- Outputs from this function are returned to the command line.
function varargout = cTFM_meshing_OutputFcn(hObject, eventdata, handles) 
% varargout  cell array for returning output args (see VARARGOUT);
% hObject    handle to figure
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Get default command line output from handles structure
varargout{1} = handles.output;

%=====================================================================
% --- Executes on clicking btnSelectFolder button.
% hObject    handle to ctfm_pushbutton_load (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)
% Asks user to select a directory and then loads up the listbox (via a call
% to LoadImageList)
function ctfm_pushbutton_load_Callback(hObject, eventdata, handles)
    % hObject    handle to btnSelectFolder (see GCBO)
    % eventdata  reserved - to be defined in a future version of MATLAB
    % handles    structure with handles and user data (see GUIDATA)
    %msgbox(handles.var.ImageFolder);
    returnValue = uigetdir(handles.var.ImageFolder,'Select folder');
	% returnValue will be 0 (a double) if they click cancel.
	% returnValue will be the path (a string) if they clicked OK.
	if returnValue ~= 0
		% Assign the value if they didn't click cancel.
		handles.var.ImageFolder = returnValue;
		handles = LoadImageList(handles);
		set(handles.ctfm_txtFolder, 'string' ,handles.var.ImageFolder);
		guidata(hObject, handles);
		% Save the image folder in our ini file.
		last_used_dir = handles.var.ImageFolder;
		save('cTFM_settings.mat', 'last_used_dir');
    end


    return

% --- If Enable == 'on', executes on mouse press in 5 pixel border.
% --- Otherwise, executes on mouse press in 5 pixel border or over ctfm_pushbutton_load.
function ctfm_pushbutton_load_ButtonDownFcn(hObject, eventdata, handles)
% hObject    handle to ctfm_pushbutton_load (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)
	


% --- Executes on selection change in ctfm_lstImageList.
function ctfm_lstImageList_Callback(hObject, eventdata, handles)
% hObject    handle to ctfm_lstImageList (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)
% Hints: contents = get(hObject,'String') returns ctfm_lstImageList contents as cell array
%        contents{get(hObject,'Value')} returns selected item from ctfm_lstImageList
    global baseImageFileName;
    global selectedListboxItem
	clear global imgOriginal;
	global imgOriginal;	% Declare global so that other functions can see it, if they also declare it global.
	
	% Get image name
    selectedListboxItem = get(handles.ctfm_lstImageList, 'value');
	if isempty(selectedListboxItem)
		% Bail out if nothing was selected.
		% Change mouse pointer (cursor) to an arrow.
        set(handles.ctfm_pbt_load_image, 'enable', 'off');    % Disable Load Image Button.        
		set(gcf,'Pointer','arrow');
		drawnow;	% Cursor won't change right away unless you do this.
		return;
	end
    % If more than one is selected, bail out.
    if length(selectedListboxItem) > 1 
        % Disable Draw new mask - not clear if there is an image being
        % displayed.
        set(handles.ctfm_pbt_load_image, 'enable', 'off');    % Disable Load Image Button.
        baseImageFileName = '';
		% Change mouse pointer (cursor) to an arrow.
		set(gcf,'Pointer','arrow')
		drawnow;	% Cursor won't change right away unless you do this.
        change_command_prompt('Only one image may be selected',handles);    
        return;
    end
    % If only one is selected, display it.
	set(handles.ctfm_pbt_load_image, 'enable', 'on');    % Enable Load Image Button.
   
    return % from lstImageList_Callback()


% --- Executes during object creation, after setting all properties.
function ctfm_lstImageList_CreateFcn(hObject, eventdata, handles)
% hObject    handle to ctfm_lstImageList (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: listbox controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end


% --- Executes on selection change in select_objective.
function select_objective_Callback(hObject, eventdata, handles)
% hObject    handle to select_objective (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: contents = cellstr(get(hObject,'String')) returns select_objective contents as cell array
%        contents{get(hObject,'Value')} returns selected item from select_objective


% --- Executes during object creation, after setting all properties.
function select_objective_CreateFcn(hObject, eventdata, handles)
% hObject    handle to select_objective (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: popupmenu controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end


%=====================================================================
% --- Load up the listbox with tif files in folder handles.var.ImageFolder
function handles=LoadImageList(handles)        
	ListOfImageNames = {};
	folder = handles.var.ImageFolder;
	if ~isempty(handles.var.ImageFolder) 
		if exist(folder,'dir') == false
			warningMessage = sprintf('Note: the folder used when this program was last run:\n%s\ndoes not exist on this computer.\nPlease run Step 1 to select an image folder.', handles.var.ImageFolder);
			msgbox(warningMessage);
			return;
		end
	else
		msgbox('No folder specified as input for function LoadImageList.');
		return;
	end
	% If it gets to here, the folder is good.
	ImageFiles = dir([handles.var.ImageFolder '/*.*']);
	for Index = 1:length(ImageFiles)
		baseFileName = ImageFiles(Index).name;
		[folder, name, extension] = fileparts(baseFileName);
		extension = upper(extension);
		switch lower(extension)
		case {'.png', '.bmp', '.jpg', '.tif', '.avi'}
			% Allow only PNG, TIF, JPG, or BMP images
			ListOfImageNames = [ListOfImageNames baseFileName];
		otherwise
		end
	end
	set(handles.ctfm_lstImageList,'string',ListOfImageNames);
    return

%=====================================================================
% Change what is displayed in the command line	
function change_command_prompt(command,handles)
    command = sprintf(command);
	set(handles.command_prompt, 'string', command);
    return

% --- Executes on button press in pbt_analyze.
function pbt_analyze_Callback(hObject, eventdata, handles)
% hObject    handle to pbt_analyze (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)
    

%% Load image and any data that is already available from previous analysis
% of the image (/[image_name]/analysis.mat)
% --- Executes on button press in ctfm_pbt_load_image.
function ctfm_pbt_load_image_Callback(hObject, eventdata, handles)
% hObject    handle to ctfm_pbt_load_image (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)
% Change mouse pointer (cursor) to an hourglass.  
	% QUIRK: use 'watch' and you'll actually get an hourglass not a watch.
    global selectedListboxItem
	set(gcf,'Pointer','watch');
	drawnow;	% Cursor won't change right away unless you do this.
    %make sure saves from previous runs are gone:
    
    ImageFolder = handles.var.ImageFolder;
    handles = rmfield(handles,'var');
    handles.var.ImageFolder = ImageFolder;
    handles.ctfm_threshold.String = [];
    handles.ctfm_set_pitch.String = [];
    handles.ctfm_set_factor.Value = 1;
    guidata(hObject,handles);
    %-----------
    ListOfImageNames = get(handles.ctfm_lstImageList, 'string');
    baseImageFileName = strcat(cell2mat(ListOfImageNames(selectedListboxItem)));
    fullImageFileName = [handles.var.ImageFolder '/' baseImageFileName];	% Prepend folder.
	handles.var.FullImageName = baseImageFileName;
    handles.var.ImageName = baseImageFileName;
	[folder, baseFileName, extension] = fileparts(fullImageFileName);
    
    %disable all fields, since new image is being loaded
    enable_mesh_field(handles,'off')
    enable_detect_field(handles, 'off')
    enable_detect_edit(handles, 'off')
    
    f_disp_control(handles,'all','off',0)
    
    %disable all display options
    set(handles.ctfm_disp_mesh, 'Value', 0);
    set(handles.ctfm_disp_nodes, 'Value', 0);
    set(handles.ctfm_disp_nodes3D, 'Value', 0);
    
	switch lower(extension)
	case {'.mov', '.wmv', '.asf','.avi'}
		msgbox('Video format files are not supported by TFM lab.');
		% Change mouse pointer (cursor) to an arrow.
		set(gcf,'Pointer','arrow');
		drawnow;	% Cursor won't change right away unless you do this.
		return;
    otherwise
		% Display the image.
		imgOriginal = DisplayImage(hObject, handles, fullImageFileName);
        
        %check availability of data
        [sReturn,handles] = f_load_data(handles,'check');
        if sReturn == 1
            set(handles.ctfm_pbt_load_data, 'enable', 'on');
        else
            set(handles.ctfm_pbt_load_data, 'enable', 'off');
        end

        %handles = guidata(hObject);
        handles.var.img = imgOriginal;
	end
	
	% If imgOriginal is empty (couldn't be read), just exit.
	if isempty(imgOriginal) 
		% Change mouse pointer (cursor) to an arrow.
		set(gcf,'Pointer','arrow');
		drawnow;	% Cursor won't change right away unless you do this.
		return;
    end

    handles.var.ImageName = baseFileName;
    
    guidata(hObject, handles);
	% Change mouse pointer (cursor) to an arrow.
	set(gcf,'Pointer','arrow');
	drawnow;	% Cursor won't change right away unless you do this.
    

%=====================================================================
% Reads FullImageFileName from disk into the axesImage axes.
function imageArray = DisplayImage(hObject, handles, FullImageFileName)
	% Read in image.
	try
		[imageArray, colorMap] = imread(FullImageFileName);
		% colorMap will have something for an indexed image (gray scale image with a stored colormap).
		% colorMap will be empty for a true color RGB image or a monochrome gray scale image.
	catch ME
		errorMessage = sprintf('Error opening image file with imread():\n%s', FullImageFileName);
		WarnUser(errorMessage);
		imageArray = [];
        set(gcf,'Pointer','arrow');
        drawnow;
		return;	% Skip the rest of this function
    end
	
    if (colorMap == [])==0
        WarnUser('Image must be gray scale')
    end
    
	try
		% Display image array in a window on the user interface.
		%axes(handles.axes_image);
		hold off;	% IMPORTANT NOTE: hold needs to be off in order for the "fit" feature to work correctly.
		
		% Here we actually display the image in the "axes_image" axes.
		axesChildHandle = imshow(imageArray,[],'InitialMagnification', 'fit', 'parent', handles.axes_image);
        f_disp_control(handles,'img','on',1)
        
		% Display a title above the image.
		[folder, basefilename, extension] = fileparts(FullImageFileName);
		extension = lower(extension);
		% Convert any underlines in the name into spaces because otherwise the character after the underline would be a subscript.
		caption = strrep([basefilename extension], '_', ' ');
		% Display the title.
		title(handles.axes_image, caption, 'FontSize', 12);
        handles.var.FileType = extension;
        guidata(hObject, handles);
		% Make it so that if they click on the image, the callback function is executed.
		% See note on QUIRK in startup code section.
		set(axesChildHandle, 'ButtonDownFcn', @axes_image_ButtonDownFcn);
		imageFolder = folder;
		setappdata(axesChildHandle, 'imageFolder', imageFolder);

		[rows columns numberOfColorChannels] = size(imageArray);
        
        assert(numberOfColorChannels==1,'Image has more than one color channel. It should be gray scale')
        
		% Get the file date
		fileInfo = dir(FullImageFileName);
		txtInfo = sprintf('%s\n\n%d lines (rows) vertically\n%d columns across\n%d color channels\n', ...
			[basefilename extension], rows, columns, numberOfColorChannels);
		% Tell user the type of image it is.
		if numberOfColorChannels == 3
			colorbar 'off';  % get rid of colorbar.
			txtInfo = sprintf('%s\nThis is a true color, RGB image.', txtInfo);
		elseif numberOfColorChannels == 1 && isempty(colorMap)
			colorbar 'off';  % get rid of colorbar.
			txtInfo = sprintf('%s\nThis is a gray scale image, with no stored color map.', txtInfo);
		elseif numberOfColorChannels == 1 && ~isempty(colorMap)
			txtInfo = sprintf('%s\nThis is an indexed image.  It has one "value" channel with a stored color map that is used to pseudocolor it.', txtInfo);
			colormap(colorMap);
			whos colorMap;
			%fprintf('About to apply the colormap...\n');
			% Thanks to Jeff Mather at the Mathworks to helping to get this working for an indexed image.
			colorbar('peer', handles.axes_image);
			%fprintf('Done applying the colormap.\n');
		end
		% Show the file time and date.
		txtInfo = sprintf('%s\n\n%s', txtInfo, fileInfo.date);
		disp(txtInfo);
        
        %image is loaded, meshing is possible
        enable_detect_field(handles,'on');
        enable_setting_field(handles,'on');
	catch ME
		errorMessage = sprintf('Error in function DisplayImage.\nError Message:\n%s', ME.message);
		WarnUser(errorMessage);
    end
    return; % from DisplayImage
   

% --- Executes on button press in ctfm_pbt_load_data.
function ctfm_pbt_load_data_Callback(hObject, eventdata, handles)
    sReturn = f_load_data(handles,'load');
    try
        handles.var.xcoords = sReturn.xcoords;
        handles.var.ycoords = sReturn.ycoords;
        handles.var.KDTree = sReturn.KDTree;
        handles.var.threshold = sReturn.threshold;
    end
    try
        handles.var.zcoords = sReturn.zcoords;
    end
    try
        handles.var.factor = sReturn.factor;
        handles.var.hex_index = sReturn.hex_index;
        handles.var.pitch = sReturn.pitch;
        enable_detect_edit(handles,'on')
        enable_mesh_field(handles,'on')
    end
    try
        handles.var.dist_error = sReturn.dist_error;
        handles.var.angle_error = sReturn.angle_error;
    end
    guidata(hObject, handles);
    
% hObject    handle to ctfm_pbt_load_data (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)
    
    
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%%%%%%%%%%%%%% SETTINGS %%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
function ctfm_set_pitch_Callback(hObject, eventdata, handles)
% hObject    handle to ctfm_set_pitch (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: get(hObject,'String') returns contents of ctfm_set_pitch as text
%        str2double(get(hObject,'String')) returns contents of ctfm_set_pitch as a double
handles.var.pitch = str2double(get(hObject,'String'));
guidata(hObject, handles);


% --- Executes during object creation, after setting all properties.
function ctfm_set_pitch_CreateFcn(hObject, eventdata, handles)
% hObject    handle to ctfm_set_pitch (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end


% --- Executes on selection change in ctfm_set_factor.
function ctfm_set_factor_Callback(hObject, eventdata, handles)
% hObject    handle to ctfm_set_factor (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: contents = cellstr(get(hObject,'String')) returns ctfm_set_factor contents as cell array
%        contents{get(hObject,'Value')} returns selected item from ctfm_set_factor
contents = cellstr(get(hObject,'String'));
iEntry = get(hObject,'Value');
factor = f_factor_mapping(contents,iEntry,'set');
if factor < 0
    %invalid selection....do nothing for now
    disp('invalid selection')
else
    handles.var.factor = factor;
end
guidata(hObject, handles);

% --- Executes during object creation, after setting all properties.
function ctfm_set_factor_CreateFcn(hObject, eventdata, handles)
% hObject    handle to ctfm_set_factor (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: popupmenu controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end

function enable_setting_field(handles,sCase)
    set(handles.ctfm_set_pitch, 'enable', sCase)
    set(handles.ctfm_set_factor, 'enable', sCase)

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%%%%%%%%%%% NODE DETECTION %%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% --- Executes on button press in ctfm_pbt_detect.
function ctfm_pbt_detect_Callback(hObject, eventdata, handles)
    % hObject    handle to ctfm_pbt_detect (see GCBO)
    % eventdata  reserved - to be defined in a future version of MATLAB
    % handles    structure with handles and user data (see GUIDATA)
    % check if all settings are available, otherwise prompt
    if detect_check(handles)==0
        return
    end
    
    threshold = handles.var.threshold;
    
    set(gcf,'Pointer','watch');
    drawnow;	% Cursor won't change right away unless you do this.
    
    
    [ycoords,xcoords]=f_dynadetection(handles.var.img,threshold);
    
    %create KDTree object
    handles.var.KDTree = createns([xcoords,ycoords]);
    handles.var.xcoords = xcoords;
    handles.var.ycoords = ycoords;
        
    %message output
    disp(['Threshold: ',num2str(threshold),...
        '; Nodes detected: ',num2str(length(xcoords))])
    
    %nodes now available & output
    handles.data.nodes = 1;
    
    set(gcf,'Pointer','arrow');
    drawnow;	% Cursor won't change right away unless you do this.    
    
    f_disp_control(handles,'nodes','on',1)
    f_axis_control(handles)
    enable_mesh_field(handles,'on')
    enable_detect_edit(handles,'on')
    guidata(hObject,handles);

% --- Executes on button press in ctfm_pbt_load_imaris.
function ctfm_pbt_load_imaris_Callback(hObject, eventdata, handles)
% hObject    handle to ctfm_pbt_load_imaris (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)    
[csvname, csvpath] = uigetfile( ...
{'*.csv;*.xls;*.xlsx',...
 'Imaris exports (*.csv,*.xls,*.xlsx)'}, ...
   'Pick a file');
[xcoords,ycoords,zcoords] = f_imaris_import(csvname, csvpath);

prompt = {'Enter objective scaling [um/px]:',};
dlg_title = 'Input';
num_lines = 1;
if isfield(handles.var,'factor')
    def = {num2str(handles.var.factor)};
else
    def = {'1'};
end

factor = inputdlg(prompt,dlg_title,num_lines,def);
factor = str2double(factor{1});

%create KDTree object
handles.var.KDTree = createns([xcoords/factor,ycoords/factor]);
handles.var.xcoords = xcoords/factor + 0.5;
handles.var.ycoords = ycoords/factor + 0.5;
handles.var.zcoords = zcoords/factor;
handles.var.threshold = 1;

enable_mesh_field(handles,'on')
enable_detect_edit(handles,'on')

f_disp_control(handles,'img','on',0)
f_disp_control(handles,'nodes3D','on',1)
f_disp_control(handles,'nodes','on',0)
f_axis_control(handles)

guidata(hObject,handles);

    
function pass = detect_check(handles)
    if isfield(handles,'var')
        if isfield(handles.var,'img')
            img = handles.var.img;       
        else
            WarnUser('Image for node detection not loaded/found')
            pass = 0;
            return;
        end
    else
        WarnUser('Image for node detection not loaded/found')
        pass = 0;
        return;
    end
    if isfield(handles.var,'threshold')
        if isnan(handles.var.threshold)
            WarnUser('Border range or threshold not set')
            pass = 0;
            return;
        else
            pass = 1;
        end
    else
        WarnUser('Threshold not set')
        pass = 0;
        return;
    end
    
% --- Executes on button press in ctfm_pbt_detect_add.
function ctfm_pbt_detect_add_Callback(hObject, eventdata, handles)
% hObject    handle to ctfm_pbt_detect_add (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

    [x,y] = f_add_node(handles.var);
    hold on
    scatter(x,y,'r');
    hold off
    
    % If z-coordinates are available the z position of the added dot is 
    % interpolated from its surrounding   
    if isfield(handles.var,'zcoords') %zcoords are defined and a z-position needed
        [IDX,~]=knnsearch(handles.var.KDTree,[x,y],'k',20);
        z = griddata(handles.var.xcoords(IDX),handles.var.ycoords(IDX),handles.var.zcoords(IDX),x,y);
        handles.var.zcoords = [handles.var.zcoords;z];
    end
    
    xcoords = handles.var.xcoords;
    xcoords = [xcoords;x];
    ycoords = handles.var.ycoords;
    ycoords = [ycoords;y];

    handles.var.xcoords = xcoords;
    handles.var.ycoords = ycoords;
    handles.var.KDTree = createns([xcoords,ycoords]);
    guidata(hObject,handles);
    
% --- Executes on button press in ctfm_pbt_detect_delete.
function ctfm_pbt_detect_delete_Callback(hObject, eventdata, handles)
% hObject    handle to ctfm_pbt_detect_delete (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

    del_ind = f_delete_node(handles.var.KDTree);
    
    xcoords = handles.var.xcoords;
    ycoords = handles.var.ycoords;
    
    hold on
    scatter(xcoords(del_ind),ycoords(del_ind),'k');
    scatter(xcoords(del_ind),ycoords(del_ind),'rx');
    hold off
    
    
    xcoords(del_ind)= [];
    ycoords(del_ind)= [];
    
    if isfield(handles.var,'zcoords') %zcoords are defined and one must also be deleted
        zcoords = handles.var.zcoords;
        zcoords(del_ind) = [];
        handles.var.zcoords = zcoords;
    end
    
    handles.var.xcoords = xcoords;
    handles.var.ycoords = ycoords;
    
    handles.var.KDTree = createns([xcoords,ycoords]);
    guidata(hObject,handles);
    
    %f_axis_control(handles);
    
    %message output
    disp(['Threshold: ',num2str(handles.var.threshold),...
        '; Nodes detected: ',num2str(length(xcoords))])
    
% --- Executes on button press in pbt_detect_save.
function pbt_detect_save_Callback(hObject, eventdata, handles)
% hObject    handle to pbt_detect_save (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)
pass = f_save(handles,'nodes');
if pass ~= 1
    WarnUser(pass);
end
    
function enable_detect_field(handles,sCase)
    set(handles.ctfm_pbt_detect, 'enable', sCase)
    set(handles.ctfm_pbt_load_imaris, 'enable', sCase)
    set(handles.ctfm_threshold, 'enable', sCase)
function enable_detect_edit(handles,sCase)
    set(handles.ctfm_pbt_detect_add, 'enable', sCase)
    set(handles.ctfm_pbt_detect_delete, 'enable', sCase)
    set(handles.ctfm_pbt_detect_save, 'enable', sCase)

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%%%%%%%%%%%% GRID MESHING %%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

function borderRange_Callback(hObject, eventdata, handles)
% hObject    handle to borderRange (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: get(hObject,'String') returns contents of borderRange as text
%        str2double(get(hObject,'String')) returns contents of borderRange as a double
handles.var.borderRange = str2double(get(hObject,'String'));
guidata(hObject, handles);

% --- Executes during object creation, after setting all properties.
function borderRange_CreateFcn(hObject, eventdata, handles)
% hObject    handle to borderRange (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end

function ctfm_threshold_Callback(hObject, eventdata, handles)
% hObject    handle to ctfm_threshold (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)
handles.var.threshold = str2double(get(hObject,'String'));
guidata(hObject, handles);

% --- Executes during object creation, after setting all properties.
function ctfm_threshold_CreateFcn(hObject, eventdata, handles)
% hObject    handle to ctfm_threshold (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end


function pass = mesh_check(handles)
    if isfield(handles.var,'dist_error') == 0
        WarnUser('Acceptable distance error for safe meshing not set')
        pass = 0;
        return;
    end
    if isfield(handles.var,'angle_error') == 0
        WarnUser('Acceptable angle error for safe meshing not set')
        pass = 0;
        return;
    end
    if isfield(handles.var,'img') == 0
        WarnUser('Image for meshing not loaded/found')
        pass = 0;
        return;
    end
    if isfield(handles.var,'pitch') == 0
        WarnUser('Pitch for meshing not set')
        pass = 0;
        return;
    end
    if isfield(handles.var,'factor') == 0
        WarnUser('Objective from imaging not set')
        pass = 0;
        return
    elseif strcmp(handles.var.factor,'select') || isempty(handles.var.factor)
        WarnUser('Objective from imaging not set')
        pass = 0;
        return;
    else
        handles.var.factor;
        pass = 1;
        return;
    end
%     if isfield(handles,'var.borderRange')
%         if isnan(handles.var.borderRange)
%             WarnUser('Border range or ctfm_threshold not set')
%             pass = 0;
%             return;
%         else
%             pass = 1;
%         end
%     else
%         WarnUser('Border range not set')
%         pass = 0;
%         return;
%     end
    
% --- Executes on button press in ctfm_pbt_mesh.
function ctfm_pbt_mesh_Callback(hObject, eventdata, handles)
% hObject    handle to ctfm_pbt_mesh (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% check if all settings are available, otherwise prompt
if mesh_check(handles)==0
    return
end


set(gcf,'Pointer','watch');
drawnow;	% Cursor won't change right away unless you do this.

%border = handles.var.borderRange;
[hex_index,hex_distance,groups,clusters,info,safe_triangles]=f_meshing(handles.var);

set(gcf,'Pointer','arrow');
drawnow;


if info.type == 1
    WarnUser('Optimal solution for one or more clusters not found');
    disp(info.description);
elseif info.type == -1
    WarnUser(info.discription)
    disp(info.description);
else
    disp(info.description);
end


f_disp_control(handles,'mesh','on',1)
f_disp_control(handles,'nodes','on',1)
f_disp_control(handles,'img','on',1)
set(handles.ctfm_disp_nodes3D, 'value', 0)
enable_mesh_field(handles,'on')

handles.var.hex_index = hex_index;
handles.var.hex_distance = hex_distance;
handles.var.groups = groups;
handles.var.clusters = clusters;
handles.var.safe_triangles = safe_triangles;
guidata(hObject,handles);



% --- Executes on button press in ctfm_pbt_mesh_add.
function ctfm_pbt_mesh_add_Callback(hObject, eventdata, handles)
% hObject    handle to ctfm_pbt_mesh_add (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

manual_conn = f_add_edge(handles.var);
handles.var.manual_conn = manual_conn;

guidata(hObject,handles);

% --- Executes on button press in ctfm_pbt_mesh_delete.
function ctfm_pbt_mesh_delete_Callback(hObject, eventdata, handles)
% hObject    handle to ctfm_pbt_mesh_delete (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

manual_conn = f_delete_edge(handles);
handles.var.manual_conn = manual_conn;

%f_axis_control(handles,'manual_conn')
guidata(hObject,handles);

% --- Executes on button press in pbt_mesh_save.
function pbt_mesh_save_Callback(hObject, eventdata, handles)
% hObject    handle to pbt_mesh_save (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)
pass = f_save(handles,'mesh');
if pass ~= 1
    WarnUser(pass);
end

function enable_mesh_field(handles,sCase)
    set(handles.ctfm_pbt_mesh_add, 'enable', sCase);
    set(handles.ctfm_pbt_mesh_delete, 'enable', sCase);
    set(handles.ctfm_pbt_mesh_save, 'enable', sCase);
    set(handles.ctfm_pbt_mesh, 'enable', sCase');



%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%%%%%%%%%%%% Info Display %%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% Warn user via the command window and a popup message.
function WarnUser(warningMessage)
	fprintf(1, '%s\n', warningMessage);
	waitfor(warndlg(warningMessage));
	return; % from WarnUser()
    
    
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%%%%%%%%%%%% Display control %%%%%%%%%%%%%%%%%%%%%%%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% --- Executes on button press in ctfm_disp_nodes.
function ctfm_disp_nodes_Callback(hObject, eventdata, handles)
% hObject    handle to ctfm_disp_nodes (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)
set(handles.ctfm_disp_nodes3D, 'Value', 0);
% Hint: get(hObject,'Value') returns toggle state of ctfm_disp_nodes


% --- Executes on button press in ctfm_disp_mesh.
function ctfm_disp_mesh_Callback(hObject, eventdata, handles)
% hObject    handle to ctfm_disp_mesh (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)
set(handles.ctfm_disp_nodes3D, 'Value', 0);
% Hint: get(hObject,'Value') returns toggle state of ctfm_disp_mesh


% --- Executes on button press in ctfm_disp_image.
function ctfm_disp_image_Callback(hObject, eventdata, handles)
% hObject    handle to ctfm_disp_image (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)
set(handles.ctfm_disp_nodes3D, 'Value', 0);
% Hint: get(hObject,'Value') returns toggle state of ctfm_disp_image


% --- Executes on button press in ctfm_disp_nodes3D.
function ctfm_disp_nodes3D_Callback(hObject, eventdata, handles)
% hObject    handle to ctfm_disp_nodes3D (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)
set(handles.ctfm_disp_nodes, 'Value', 0);
set(handles.ctfm_disp_image, 'Value', 0);
set(handles.ctfm_disp_mesh, 'Value', 0);
% Hint: get(hObject,'Value') returns toggle state of ctfm_disp_nodes3D


% --- Executes on button press in ctfm_disp_apply.
function ctfm_disp_apply_Callback(hObject, eventdata, handles)
% hObject    handle to ctfm_disp_apply (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)
set(gcf,'Pointer','watch');
drawnow;	% Cursor won't change right away unless you do this.
f_axis_control(handles)
set(gcf,'Pointer','arrow');
drawnow;

% --- Executes on button press in ctfm_pbt_export.
function ctfm_pbt_export_Callback(hObject, eventdata, handles)
% hObject    handle to ctfm_pbt_export (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)
set(gcf,'Pointer','watch');
drawnow;	

pitch = handles.var.pitch;
factor = handles.var.factor;
img = handles.var.img;
xcoords = handles.var.xcoords;
ycoords = handles.var.ycoords;
try
    zcoords = handles.var.zcoords;
end
triangles = f_hex2tri(handles.var.hex_index);
if exist([handles.var.ImageFolder,'/',handles.var.ImageName],'dir')==0
    %create directory if needed
    mkdir(handles.var.ImageFolder,handles.var.ImageName)
end
if exist('zcoords')
    save([handles.var.ImageFolder,'/',handles.var.ImageName,'/',handles.var.ImageName,'_Meshing_data.mat'],'img','pitch','factor','xcoords','ycoords','zcoords','triangles')
else
    save([handles.var.ImageFolder,'/',handles.var.ImageName,'/',handles.var.ImageName,'_Meshing_data.mat'],'img','pitch','factor','xcoords','ycoords','triangles')
end

set(gcf,'Pointer','arrow');
drawnow;
disp('Exporting data complete')





% --- Executes on button press in ctfm_pbt_mesh_save.
function ctfm_pbt_mesh_save_Callback(hObject, eventdata, handles)
% hObject    handle to ctfm_pbt_mesh_save (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)
pass = f_save(handles,'mesh');
if pass ~= 1
    WarnUser(pass);
end

% --- Executes on button press in ctfm_pbt_detect_save.
function ctfm_pbt_detect_save_Callback(hObject, eventdata, handles)
% hObject    handle to ctfm_pbt_detect_save (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)
pass = f_save(handles,'nodes');
if pass ~= 1
    WarnUser(pass);
end

function ctfm_dist_error_Callback(hObject, eventdata, handles)
% hObject    handle to ctfm_dist_error (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: get(hObject,'String') returns contents of ctfm_dist_error as text
%        str2double(get(hObject,'String')) returns contents of ctfm_dist_error as a double
handles.var.dist_error = str2double(get(hObject,'String'));
guidata(hObject, handles);

% --- Executes during object creation, after setting all properties.
function ctfm_dist_error_CreateFcn(hObject, eventdata, handles)
% hObject    handle to ctfm_dist_error (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end



function ctfm_angle_error_Callback(hObject, eventdata, handles)
% hObject    handle to ctfm_angle_error (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: get(hObject,'String') returns contents of ctfm_angle_error as text
%        str2double(get(hObject,'String')) returns contents of ctfm_angle_error as a double
handles.var.angle_error = str2double(get(hObject,'String'));
guidata(hObject, handles);

% --- Executes during object creation, after setting all properties.
function ctfm_angle_error_CreateFcn(hObject, eventdata, handles)
% hObject    handle to ctfm_angle_error (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end
