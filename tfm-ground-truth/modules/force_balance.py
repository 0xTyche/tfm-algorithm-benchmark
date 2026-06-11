"""三力平衡求解：给定 F1、F2 及 F3 的几何约束，计算满足 ΣF=0, ΣMz=0 的 F3。"""

import numpy as np


def calculate_force_components(magnitude, angle_deg):
    """
    根据力的大小和角度计算分量
    
    参数:
        magnitude (float): 集中力的大小 (N)
        angle_deg (float): 方向角 (度,逆时针,0°为x正向)
    
    返回:
        tuple: (Fx, Fy) 力在x和y方向的分量 (N)
    
    示例:
        >>> Fx, Fy = calculate_force_components(10, 45)
        >>> print(f"Fx={Fx:.2f}, Fy={Fy:.2f}")
        Fx=7.07, Fy=7.07
    """
    angle_rad = np.deg2rad(angle_deg)
    Fx = magnitude * np.cos(angle_rad)
    Fy = magnitude * np.sin(angle_rad)
    
    return Fx, Fy


def calculate_third_force(force1, force2, force3_pos):
    """
    计算第三个力以满足力和力矩平衡
    
    参数:
        force1 (dict): 力1的字典 {'magnitude', 'angle_deg', 'position', 'square_size'}
        force2 (dict): 力2的字典 {'magnitude', 'angle_deg', 'position', 'square_size'}
        force3_pos (dict): 力3的位置和尺寸 {'position', 'square_size'}
    
    返回:
        dict: 完整的力3字典,包含计算得到的magnitude和angle_deg
    
    注意:
        此函数基于力平衡方程计算力3的分量和大小
        力矩平衡将在verify_equilibrium函数中验证
    
    示例:
        >>> force1 = {'magnitude': 18, 'angle_deg': 135, 'position': (150, 190), 'square_size': 80}
        >>> force2 = {'magnitude': 18, 'angle_deg': 45, 'position': (360, 220), 'square_size': 80}
        >>> force3_pos = {'position': (260, 340), 'square_size': 70}
        >>> force3 = calculate_third_force(force1, force2, force3_pos)
        >>> print(f"Force3: {force3['magnitude']:.2f} Pa at {force3['angle_deg']:.2f}°")
    """
    F1x, F1y = calculate_force_components(force1['magnitude'], force1['angle_deg'])
    F2x, F2y = calculate_force_components(force2['magnitude'], force2['angle_deg'])

    # ΣFx = 0, ΣFy = 0
    F3x = -(F1x + F2x)
    F3y = -(F1y + F2y)

    F3_magnitude = np.sqrt(F3x**2 + F3y**2)
    F3_angle_deg = np.rad2deg(np.arctan2(F3y, F3x))

    force3 = {
        'magnitude': F3_magnitude,
        'angle_deg': F3_angle_deg,
        'position': force3_pos['position'],
        'square_size': force3_pos['square_size'],
        'Fx': F3x,
        'Fy': F3y
    }
    
    return force3


def verify_equilibrium(forces, reference_point=(0, 0), tolerance=1e-3):
    """
    验证力和力矩平衡
    
    参数:
        forces (list): 力的列表,每个力包含magnitude, angle_deg, position
        reference_point (tuple): 力矩参考点,默认(0, 0)
        tolerance (float): 平衡判断的容差,默认1e-3
    
    返回:
        dict: 结果字典
            {
                'sum_Fx': float,       # x方向力的总和 (N)
                'sum_Fy': float,       # y方向力的总和 (N)
                'sum_Mz': float,       # z轴力矩总和 (N·pixel ≡ N·μm)
                'is_balanced': bool,   # 是否平衡
                'force_details': list  # 每个力的详细信息
            }
    
    注意:
        力矩计算公式: Mz = x*Fy - y*Fx (绕z轴,右手定则)
    
    示例:
        >>> forces = [force1, force2, force3]
        >>> result = verify_equilibrium(forces)
        >>> if result['is_balanced']:
        ...     print("系统处于平衡状态")
    """
    sum_Fx = 0.0
    sum_Fy = 0.0
    sum_Mz = 0.0
    force_details = []

    for i, force in enumerate(forces, 1):
        if 'Fx' in force and 'Fy' in force:
            Fx = force['Fx']
            Fy = force['Fy']
        else:
            Fx, Fy = calculate_force_components(force['magnitude'], force['angle_deg'])
        
        x, y = force['position']
        x_rel = x - reference_point[0]
        y_rel = y - reference_point[1]

        # Mz = x*Fy - y*Fx
        Mz = x_rel * Fy - y_rel * Fx

        sum_Fx += Fx
        sum_Fy += Fy
        sum_Mz += Mz

        force_details.append({
            'force_number': i,
            'Fx': Fx,
            'Fy': Fy,
            'position': (x, y),
            'Mz': Mz
        })
    
    is_balanced = (abs(sum_Fx) < tolerance and
                   abs(sum_Fy) < tolerance and 
                   abs(sum_Mz) < tolerance)
    
    return {
        'sum_Fx': sum_Fx,
        'sum_Fy': sum_Fy,
        'sum_Mz': sum_Mz,
        'is_balanced': is_balanced,
        'force_details': force_details,
        'reference_point': reference_point,
        'tolerance': tolerance
    }


def find_balanced_position_for_force3(force1, force2, force3_size, y3=None):
    """
    计算满足力和力矩平衡的力3位置
    
    参数:
        force1 (dict): 力1的字典（包含Fx, Fy, position）
        force2 (dict): 力2的字典（包含Fx, Fy, position）
        force3_size (float): 力3的正方形边长
        y3 (float): 指定的y坐标，如果为None则自动选择合理值
    
    返回:
        dict: 包含position和explanation的字典，如果无解则返回None
    
    理论说明:
        对于三力平衡，当F1和F2确定后：
        1. F3的大小和方向由力平衡唯一确定：F3 = -(F1 + F2)
        2. F3的位置需要满足力矩平衡方程
        
        力矩平衡方程（绕原点）：
        x1·F1y - y1·F1x + x2·F2y - y2·F2x + x3·F3y - y3·F3x = 0
        
        这是一个关于(x3, y3)的线性方程，有无穷多解（一条直线）
        我们选择一个合理的解
    """
    # 获取F1和F2的信息
    F1x = force1['Fx']
    F1y = force1['Fy']
    x1, y1 = force1['position']
    
    F2x = force2['Fx']
    F2y = force2['Fy']
    x2, y2 = force2['position']
    
    # 计算F3的分量（由力平衡确定）
    F3x = -(F1x + F2x)
    F3y = -(F1y + F2y)
    
    # 力矩平衡方程: M1 + M2 + M3 = 0
    # 其中 M1 = x1·F1y - y1·F1x, M2 = x2·F2y - y2·F2x
    # M3 = x3·F3y - y3·F3x
    
    M1 = x1 * F1y - y1 * F1x
    M2 = x2 * F2y - y2 * F2x
    M12 = M1 + M2  # F1和F2产生的总力矩
    
    # 需要满足: x3·F3y - y3·F3x = -M12
    # 即: x3·F3y - y3·F3x + M12 = 0
    
    # 特殊情况处理
    if abs(F3y) < 1e-10 and abs(F3x) < 1e-10:
        return None  # F3为零，无解
    
    # 如果没有指定y3，选择一个合理的y3
    # 选择F1和F2中点附近的y坐标
    if y3 is None:
        y3 = (y1 + y2) / 2
    
    # 从力矩平衡方程求解x3
    # x3·F3y = y3·F3x - M12
    
    if abs(F3y) > 1e-10:
        # 可以从F3y求解x3
        x3 = (y3 * F3x - M12) / F3y
        
        explanation = f"给定 y₃={y3:.1f} pixel，通过力矩平衡方程计算得 x₃={x3:.2f} pixel"
    elif abs(F3x) > 1e-10:
        # F3y≈0，从F3x求解y3
        y3 = (x3 * F3y + M12) / F3x if y3 is None else y3
        x3 = (x1 + x2) / 2  # 选择一个合理的x3
        
        explanation = f"F3y≈0，选择 x₃={x3:.2f} pixel，通过力矩平衡方程计算得 y₃={y3:.2f} pixel"
    else:
        return None
    
    return {
        'position': (x3, y3),
        'square_size': force3_size,
        'explanation': explanation,
        'force_components': (F3x, F3y)
    }


def format_equilibrium_result(equilibrium_result):
    """
    格式化平衡验证结果为可读文本
    
    参数:
        equilibrium_result (dict): verify_equilibrium函数的返回值
    
    返回:
        str: 格式化的文本结果
    """
    result_text = "=" * 50 + "\n"
    result_text += "力和力矩平衡验证\n"
    result_text += "=" * 50 + "\n\n"
    
    result_text += f"参考点: ({equilibrium_result['reference_point'][0]:.1f}, "
    result_text += f"{equilibrium_result['reference_point'][1]:.1f}) pixel\n\n"
    
    # 力平衡（转换为μN显示）
    sum_Fx_uN = equilibrium_result['sum_Fx'] * 1e6
    sum_Fy_uN = equilibrium_result['sum_Fy'] * 1e6
    sum_Mz_uN = equilibrium_result['sum_Mz'] * 1e6
    
    result_text += "力平衡:\n"
    result_text += f"  ΣFx = {sum_Fx_uN:>12.6f} μN\n"
    result_text += f"  ΣFy = {sum_Fy_uN:>12.6f} μN\n\n"
    
    # 力矩平衡
    result_text += "力矩平衡:\n"
    result_text += f"  ΣMz = {sum_Mz_uN:>12.6f} μN·μm\n\n"
    
    # 平衡状态
    if equilibrium_result['is_balanced']:
        result_text += "✅ 系统处于平衡状态\n"
    else:
        result_text += "❌ 系统不平衡\n"
        result_text += f"   建议: 调整力3的位置或前两个力的参数\n"
    
    result_text += "\n" + "=" * 50 + "\n"
    
    return result_text

