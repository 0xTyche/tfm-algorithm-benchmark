"""力/牵引及位移场数据的 MAT 文件导出。"""

import numpy as np
from scipy.io import savemat
from datetime import datetime


def export_forces_to_mat(forces, params, filename='forces_data.mat'):
    """
    导出力数据到MAT文件
    
    参数:
        forces (list): 力的列表,包含3个力的字典
        params (dict): 计算参数字典,包含材料参数和场设置
        filename (str): 输出文件名
    
    文件结构:
        forces_data.mat包含一个结构体,包括:
        - description: 描述信息
        - timestamp: 时间戳
        - units: 单位说明
        - material_parameters: 材料参数
        - field_settings: 场设置
        - force1, force2, force3: 三个力的详细信息
        - equilibrium_check: 平衡验证结果
    
    返回:
        str: 保存的文件路径
    
    示例:
        >>> params = {'E': 5000, 'nu': 0.5, 'field_width': 500, ...}
        >>> forces = [force1, force2, force3]
        >>> export_forces_to_mat(forces, params, 'my_forces.mat')
    """
    export_data = {
        'description': 'Force positions, magnitudes and directions data',
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'units': {
            'position': 'pixel',
            'force': 'Pascal',
            'angle': 'degree',
            'youngs_modulus': 'Pascal'
        },
        'material_parameters': {
            'E': params.get('E', 0) * 1000,  # 转换kPa到Pa
            'nu': params.get('nu', 0)
        },
        'field_settings': {
            'width': params.get('field_width', 0),
            'height': params.get('field_height', 0),
            'boundary': params.get('boundary', 0),
            'sampling_interval': params.get('sampling_interval', 0)
        }
    }
    
    for i, force in enumerate(forces, 1):
        force_data = {
            'magnitude': force.get('magnitude', 0),
            'angle_deg': force.get('angle_deg', 0),
            'position': np.array(force.get('position', (0, 0))),
            'square_size': force.get('square_size', 0),
            'Fx': force.get('Fx', 0),
            'Fy': force.get('Fy', 0),
            'status': 'computed' if i == 3 else 'input'
        }
        export_data[f'force{i}'] = force_data
    
    if 'equilibrium_result' in params:
        eq_result = params['equilibrium_result']
        export_data['equilibrium_check'] = {
            'sum_Fx': eq_result.get('sum_Fx', 0),
            'sum_Fy': eq_result.get('sum_Fy', 0),
            'sum_Mz': eq_result.get('sum_Mz', 0),
            'is_balanced': eq_result.get('is_balanced', False)
        }
    
    savemat(filename, {'forces_data': export_data}, do_compression=True)
    return filename


def export_displacement_to_mat(pos, vec, filename='displacement_field.mat'):
    """
    导出位移数据到MAT文件(简化格式)
    
    参数:
        pos (np.ndarray): N×2 位置矩阵 [[x1,y1], [x2,y2], ...]
        vec (np.ndarray): N×2 位移矩阵 [[ux1,uy1], [ux2,uy2], ...]
        filename (str): 输出文件名
    
    文件结构:
        displacement_field.mat包含两个变量:
        - pos: N×2 矩阵,每行是[x, y]坐标
        - vec: N×2 矩阵,每行是[ux, uy]位移
    
    返回:
        str: 保存的文件路径
    
    MATLAB读取示例:
        load('displacement_field.mat');
        x_coords = pos(:, 1);
        y_coords = pos(:, 2);
        u_x = vec(:, 1);
        u_y = vec(:, 2);
    
    示例:
        >>> X, Y = np.meshgrid(x_vec, y_vec)
        >>> pos = np.column_stack([X.flatten(), Y.flatten()])
        >>> vec = np.column_stack([u_x.flatten(), u_y.flatten()])
        >>> export_displacement_to_mat(pos, vec, 'my_displacement.mat')
    """
    # 验证输入形状
    if pos.shape[1] != 2 or vec.shape[1] != 2:
        raise ValueError("pos和vec必须是N×2矩阵")
    
    if pos.shape[0] != vec.shape[0]:
        raise ValueError("pos和vec的行数必须相同")
    
    savemat(filename, {'pos': pos, 'vec': vec}, do_compression=True)
    return filename


def export_displacement_full(X, Y, u_x, u_y, forces, params, filename='displacement_full.mat'):
    """
    导出完整的位移场数据(包含网格和元数据)
    
    参数:
        X, Y (np.ndarray): 网格坐标矩阵
        u_x, u_y (np.ndarray): 位移场分量
        forces (list): 力的列表
        params (dict): 计算参数
        filename (str): 输出文件名
    
    返回:
        str: 保存的文件路径
    """
    u_magnitude = np.sqrt(u_x**2 + u_y**2)
    export_data = {
        'description': 'Full displacement field data with grid and metadata',
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'grid': {
            'X': X,
            'Y': Y,
            'shape': np.array(X.shape)
        },
        'displacement': {
            'u_x': u_x,
            'u_y': u_y,
            'u_magnitude': u_magnitude
        },
        'material_parameters': {
            'E': params.get('E', 0) * 1000,  # 转换kPa到Pa
            'nu': params.get('nu', 0)
        },
        'statistics': {
            'max_displacement': np.max(u_magnitude),
            'min_displacement': np.min(u_magnitude),
            'mean_displacement': np.mean(u_magnitude),
            'max_ux': np.max(np.abs(u_x)),
            'max_uy': np.max(np.abs(u_y))
        }
    }
    
    savemat(filename, {'displacement_data': export_data}, do_compression=True)
    return filename


def prepare_displacement_export(X, Y, u_x, u_y):
    """
    准备位移场数据用于导出(简化格式)
    
    参数:
        X, Y (np.ndarray): 网格坐标矩阵
        u_x, u_y (np.ndarray): 位移场分量
    
    返回:
        tuple: (pos, vec)
            pos: N×2 位置矩阵
            vec: N×2 位移矩阵
    
    示例:
        >>> pos, vec = prepare_displacement_export(X, Y, u_x, u_y)
        >>> export_displacement_to_mat(pos, vec)
    """
    # 展平为列向量 (列优先,与MATLAB meshgrid一致)
    pos = np.column_stack([X.flatten(), Y.flatten()])
    vec = np.column_stack([u_x.flatten(), u_y.flatten()])
    
    return pos, vec

