"""数值稳定性辅助函数和输入参数验证。"""

import numpy as np


def safe_log(numerator, denominator, eps=1e-10):
    """
    安全对数函数,避免除零和负数
    
    参数:
        numerator (float or np.ndarray): 分子
        denominator (float or np.ndarray): 分母
        eps (float): 正则化参数,默认1e-10
    
    返回:
        float or np.ndarray: log(|numerator + eps| / |denominator + eps|)
    
    示例:
        >>> safe_log(10, 5)
        0.6931471805599453
    """
    num = np.abs(numerator) + eps
    den = np.abs(denominator) + eps
    return np.log(num / den)


def safe_distance(dx, dy, eps=1e-10):
    """
    安全距离计算,避免除零
    
    参数:
        dx (float or np.ndarray): x方向距离
        dy (float or np.ndarray): y方向距离
        eps (float): 正则化参数,默认1e-10
    
    返回:
        float or np.ndarray: sqrt(dx^2 + dy^2 + eps)
    
    示例:
        >>> safe_distance(3, 4)
        5.0
    """
    return np.sqrt(dx**2 + dy**2 + eps)


def is_inside_square(x, y, x_c, y_c, a):
    """
    判断点是否在正方形内部
    
    参数:
        x (float or np.ndarray): 观察点x坐标
        y (float or np.ndarray): 观察点y坐标
        x_c (float): 正方形中心x坐标
        y_c (float): 正方形中心y坐标
        a (float): 正方形半边长
    
    返回:
        bool or np.ndarray: True表示在正方形内部
    
    示例:
        >>> is_inside_square(10, 10, 0, 0, 5)
        False
    """
    return (np.abs(x - x_c) < a) & (np.abs(y - y_c) < a)


def validate_inputs(params):
    """
    验证用户输入的参数
    
    参数:
        params (dict): 包含所有输入参数的字典
    
    返回:
        tuple: (is_valid, error_message)
            is_valid (bool): 输入是否有效
            error_message (str): 错误信息,如果有效则为空字符串
    
    示例:
        >>> params = {'E': 5000, 'nu': 0.5, 'field_width': 500}
        >>> is_valid, msg = validate_inputs(params)
        >>> print(is_valid)
        True
    """
    errors = []
    
    # 检查杨氏模量
    if 'E' in params:
        if params['E'] <= 0:
            errors.append("❌ 杨氏模量必须大于0")
    
    # 检查泊松比
    if 'nu' in params:
        if not (-1 <= params['nu'] <= 0.5):
            errors.append("⚠️ 泊松比通常在-1到0.5之间")
    
    # 检查场尺寸
    if 'field_width' in params and params['field_width'] <= 0:
        errors.append("❌ 场宽度必须大于0")
    if 'field_height' in params and params['field_height'] <= 0:
        errors.append("❌ 场高度必须大于0")
    
    # 检查力的大小
    for i in [1, 2]:
        key = f'force{i}_magnitude'
        if key in params and params[key] < 0:
            errors.append(f"❌ 力{i}的大小不能为负数")
    
    # 检查正方形尺寸
    for i in [1, 2, 3]:
        key = f'force{i}_size'
        if key in params and params[key] <= 0:
            errors.append(f"❌ 力{i}的正方形边长必须大于0")
    
    # 检查位置是否在场范围内
    if 'field_width' in params and 'field_height' in params and 'boundary' in params:
        width = params['field_width']
        height = params['field_height']
        boundary = params['boundary']
        
        for i in [1, 2, 3]:
            x_key = f'force{i}_x'
            y_key = f'force{i}_y'
            if x_key in params and y_key in params:
                x = params[x_key]
                y = params[y_key]
                if not (boundary <= x <= width - boundary):
                    errors.append(f"❌ 力{i}的x位置超出有效计算区域")
                if not (boundary <= y <= height - boundary):
                    errors.append(f"❌ 力{i}的y位置超出有效计算区域")
    
    if errors:
        return False, "\n".join(errors)
    else:
        return True, ""


def check_squares_overlap(forces):
    """
    检查力作用区域是否存在重叠
    
    参数:
        forces (list): 力的列表,每个力是包含position和square_size的字典
    
    返回:
        bool: True表示存在重叠
    
    示例:
        >>> force1 = {'position': (100, 100), 'square_size': 50}
        >>> force2 = {'position': (200, 200), 'square_size': 50}
        >>> check_squares_overlap([force1, force2])
        False
    """
    for i in range(len(forces)):
        for j in range(i + 1, len(forces)):
            x1, y1 = forces[i]['position']
            a1 = forces[i]['square_size'] / 2
            
            x2, y2 = forces[j]['position']
            a2 = forces[j]['square_size'] / 2
            
            # 检查是否重叠:两个正方形的中心距离小于半边长之和
            dx = abs(x1 - x2)
            dy = abs(y1 - y2)
            
            if dx < (a1 + a2) and dy < (a1 + a2):
                return True
    
    return False

