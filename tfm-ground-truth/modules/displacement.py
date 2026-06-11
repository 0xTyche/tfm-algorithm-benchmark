"""BIS 位移场计算：方形均匀牵引区域在弹性半空间表面产生的解析位移。"""

import numpy as np
from utils.helpers import safe_log


def compute_displacement_square(x, y, a, p, E, nu):
    """
    计算正方形区域[-a,a]×[-a,a]上均布力p在点(x,y)产生的位移
    
    基于Boussinesq解的积分形式,使用README中的公式计算位移场。
    
    参数:
        x (float or np.ndarray): 观察点x坐标,相对于正方形中心 (pixel ≡ μm)
        y (float or np.ndarray): 观察点y坐标,相对于正方形中心 (pixel ≡ μm)
        a (float): 正方形半边长 (pixel ≡ μm)
        p (float): 均布牵引应力密度 (N/pixel² ≡ Pa，假设1 pixel=1μm)
        E (float): 杨氏模量 (Pa ≡ N/μm²)
        nu (float): 泊松比 (无量纲)
    
    返回:
        tuple: (u, v)
            u (float or np.ndarray): x方向位移 (pixel ≡ μm)
            v (float or np.ndarray): y方向位移 (pixel ≡ μm)
    
    注意:
        - 坐标系原点在正方形中心
        - 当观察点非常接近正方形边界时可能出现数值不稳定
        - 使用safe_log函数避免对数奇异性
    
    示例:
        >>> u, v = compute_displacement_square(10, 20, 5, 1.0, 5000, 0.5)
        >>> print(f"位移: ({u:.6f}, {v:.6f})")
    """
    # 计算四个角点到观察点的距离
    # R1: 右上角 (a-x, a-y)
    # R2: 右下角 (a-x, -a-y)
    # R3: 左上角 (-a-x, a-y)
    # R4: 左下角 (-a-x, -a-y)
    R1 = np.sqrt((a - x)**2 + (a - y)**2)
    R2 = np.sqrt((a - x)**2 + (a + y)**2)
    R3 = np.sqrt((a + x)**2 + (a - y)**2)
    R4 = np.sqrt((a + x)**2 + (a + y)**2)
    
    # 计算水平位移 u(x,y)
    # 根据README公式(1.12)
    
    # 第一项: 与y坐标相关的对数项
    term1_u = 2 * ((a - y) * safe_log((a - x) + R1, (-a - x) + R3)
                   - (-a - y) * safe_log((a - x) + R2, (-a - x) + R4))
    
    # 第二项: 与x坐标相关的对数项
    term2_u = ((a - x) * safe_log((a - y) + R1, (-a - y) + R2)
               - (-a - x) * safe_log((a - y) + R3, (-a - y) + R4))
    
    # 第三项: 泊松比修正项
    term3_u = (1 - 2*nu) * ((a - x) * safe_log((a - y) + R1, (-a - y) + R2)
                             - (-a - x) * safe_log((a - y) + R3, (-a - y) + R4))
    
    # 组合所有项计算u
    u = (p * (1 + nu) / (2 * np.pi * E)) * (term1_u + term2_u + term3_u)
    
    # 计算垂直位移 v(x,y)
    # 根据README公式
    v = (p * nu * (1 + nu) / (np.pi * E)) * (-R1 + R2 + R3 - R4)
    
    return u, v


def compute_displacement_square_si(x_m, y_m, a_m, p_pa, E_pa, nu):
    """
    SI单位版本：计算正方形区域[-a,a]×[-a,a]上均匀牵引应力p(Pa)在点(x,y)产生的位移（m）

    参数:
        x_m, y_m: 观察点相对正方形中心坐标（m）
        a_m: 正方形半边长（m）
        p_pa: 均匀牵引应力（Pa = N/m^2）
        E_pa: 杨氏模量（Pa）
        nu: 泊松比

    返回:
        (u_m, v_m): 位移（m）
    """
    # 计算四个角点到观察点的距离（m）
    R1 = np.sqrt((a_m - x_m)**2 + (a_m - y_m)**2)
    R2 = np.sqrt((a_m - x_m)**2 + (a_m + y_m)**2)
    R3 = np.sqrt((a_m + x_m)**2 + (a_m - y_m)**2)
    R4 = np.sqrt((a_m + x_m)**2 + (a_m + y_m)**2)

    # 水平位移 u(x,y)（SI）
    term1_u = 2 * ((a_m - y_m) * safe_log((a_m - x_m) + R1, (-a_m - x_m) + R3)
                   - (-a_m - y_m) * safe_log((a_m - x_m) + R2, (-a_m - x_m) + R4))

    term2_u = ((a_m - x_m) * safe_log((a_m - y_m) + R1, (-a_m - y_m) + R2)
               - (-a_m - x_m) * safe_log((a_m - y_m) + R3, (-a_m - y_m) + R4))

    term3_u = (1 - 2 * nu) * ((a_m - x_m) * safe_log((a_m - y_m) + R1, (-a_m - y_m) + R2)
                               - (-a_m - x_m) * safe_log((a_m - y_m) + R3, (-a_m - y_m) + R4))

    u_m = (p_pa * (1 + nu) / (2 * np.pi * E_pa)) * (term1_u + term2_u + term3_u)

    # 垂直位移 v(x,y)（SI）
    v_m = (p_pa * nu * (1 + nu) / (np.pi * E_pa)) * (-R1 + R2 + R3 - R4)

    return u_m, v_m


def compute_displacement_from_force_component_si(
    X_px,
    Y_px,
    force_pos_px,
    half_size_px,
    p_pa,
    E_pa,
    nu,
    pixel_size_um,
    direction="x",
):
    """
    SI单位版本：在规则网格上计算单个牵引应力分量产生的位移，并转换回pixel。

    - 输入网格/几何仍用pixel表示（符合UI）
    - 内部计算用SI（m, Pa）
    - 输出位移用pixel（方便显示/导出/生成图像）
    """
    length_scale_m = float(pixel_size_um) * 1e-6  # m/px
    if not np.isfinite(length_scale_m) or length_scale_m <= 0:
        raise ValueError(f"pixel_size_um 必须为正数，当前: {pixel_size_um}")

    x_c, y_c = force_pos_px
    x_rel_m = (X_px - x_c) * length_scale_m
    y_rel_m = (Y_px - y_c) * length_scale_m
    a_m = half_size_px * length_scale_m

    if direction == "x":
        u_m, v_m = compute_displacement_square_si(x_rel_m, y_rel_m, a_m, p_pa, E_pa, nu)
    else:
        # y方向牵引应力：坐标交换 + 结果交换（保持与旧实现一致）
        v_m, u_m = compute_displacement_square_si(y_rel_m, x_rel_m, a_m, p_pa, E_pa, nu)

    # m -> px
    u_px = u_m / length_scale_m
    v_px = v_m / length_scale_m
    return u_px, v_px


def compute_displacement_field_si(X, Y, forces, E_pa, nu, pixel_size_um=1.0):
    """
    用SI单位自洽地计算位移场（推荐/贴近论文实现）。

    约定:
        - 网格坐标 X,Y：pixel
        - 力的输入 forces：总力分量 Fx,Fy（N），作用区域 square_size（pixel）
        - pixel_size_um：每个pixel对应的物理长度（μm/pixel）
        - E_pa：杨氏模量（Pa）

    计算:
        - 将每个区域的总力换算为均匀牵引应力 p = F / A（Pa），其中 A=(square_size*pixel_size)^2
        - 用SI公式计算位移（m），最后转换回pixel输出

    返回:
        (u_x_px, u_y_px)
    """
    u_x_total = np.zeros_like(X, dtype=float)
    u_y_total = np.zeros_like(Y, dtype=float)

    length_scale_m = float(pixel_size_um) * 1e-6
    if not np.isfinite(length_scale_m) or length_scale_m <= 0:
        raise ValueError(f"pixel_size_um 必须为正数，当前: {pixel_size_um}")

    for i, force in enumerate(forces):
        Fx = float(force.get("Fx", 0.0))
        Fy = float(force.get("Fy", 0.0))
        position = force["position"]
        square_size = float(force["square_size"])
        half_size = square_size / 2.0

        area_m2 = (square_size * length_scale_m) ** 2
        if area_m2 <= 0:
            continue

        p_x = Fx / area_m2  # Pa
        p_y = Fy / area_m2  # Pa

        u_x_from_px, u_y_from_px = compute_displacement_from_force_component_si(
            X, Y, position, half_size, p_x, E_pa, nu, pixel_size_um, direction="x"
        )
        u_x_from_py, u_y_from_py = compute_displacement_from_force_component_si(
            X, Y, position, half_size, p_y, E_pa, nu, pixel_size_um, direction="y"
        )

        u_x_total += (u_x_from_px + u_x_from_py)
        u_y_total += (u_y_from_px + u_y_from_py)

    return u_x_total, u_y_total


def compute_displacement_from_force_component(X, Y, force_pos, half_size, p, E, nu, direction='x'):
    """
    计算单个力分量在网格上产生的位移场
    
    参数:
        X, Y (np.ndarray): 网格坐标矩阵
        force_pos (tuple): 力的中心位置 (x_c, y_c)
        half_size (float): 正方形半边长 a
        p (float): 均布牵引力密度 (Pa)
        E (float): 杨氏模量 (Pa)
        nu (float): 泊松比
        direction (str): 力的方向,'x' 或 'y'
    
    返回:
        tuple: (u_x, u_y) 该力分量在x和y方向产生的位移
    """
    x_c, y_c = force_pos
    
    # 将观察点坐标转换为相对于正方形中心的坐标
    x_rel = X - x_c
    y_rel = Y - y_c
    
    if direction == 'x':
        # x方向力分量的贡献
        u_x, u_y = compute_displacement_square(x_rel, y_rel, half_size, p, E, nu)
    else:  # direction == 'y'
        # y方向力分量需要坐标交换
        # 交换坐标: (x', y') -> (y', x')
        # 计算位移,然后交换结果: (u, v) -> (v, u)
        u_y, u_x = compute_displacement_square(y_rel, x_rel, half_size, p, E, nu)
    
    return u_x, u_y


def compute_displacement_from_force(X, Y, force, E, nu):
    """
    计算单个力在网格上产生的位移场
    
    参数:
        X, Y (np.ndarray): 网格坐标矩阵
        force (dict): 力的字典,包含:
            - 'Fx': x方向集中力分量 (N)
            - 'Fy': y方向集中力分量 (N)
            - 'position': (x, y) 位置 (pixel ≡ μm)
            - 'square_size': 正方形边长 (pixel ≡ μm)
        E (float): 杨氏模量 (Pa ≡ N/μm²)
        nu (float): 泊松比
    
    返回:
        tuple: (u_x, u_y) 位移场矩阵
    
    注意:
        该函数将x和y方向的力分量分别计算位移,然后叠加
    """
    Fx = force['Fx']
    Fy = force['Fy']
    position = force['position']
    square_size = force['square_size']
    half_size = square_size / 2
    
    # 计算均布牵引力密度
    area = square_size ** 2
    px = Fx / area  # x方向牵引力密度
    py = Fy / area  # y方向牵引力密度
    
    # x方向力分量的贡献
    u_x_from_Fx, u_y_from_Fx = compute_displacement_from_force_component(
        X, Y, position, half_size, px, E, nu, direction='x'
    )
    
    # y方向力分量的贡献
    u_x_from_Fy, u_y_from_Fy = compute_displacement_from_force_component(
        X, Y, position, half_size, py, E, nu, direction='y'
    )
    
    # 叠加两个分量的贡献
    u_x_total = u_x_from_Fx + u_x_from_Fy
    u_y_total = u_y_from_Fx + u_y_from_Fy
    
    return u_x_total, u_y_total


def compute_displacement_field(X, Y, forces, E, nu):
    """
    计算所有力产生的总位移场
    
    参数:
        X, Y (np.ndarray): 网格坐标矩阵
        forces (list): 所有力的列表,每个力是一个字典
        E (float): 杨氏模量 (Pa)
        nu (float): 泊松比
    
    返回:
        tuple: (u_x, u_y) 总位移场矩阵
    
    注意:
        使用叠加原理,将所有力产生的位移相加
    
    示例:
        >>> import numpy as np
        >>> x = np.linspace(0, 500, 50)
        >>> y = np.linspace(0, 500, 50)
        >>> X, Y = np.meshgrid(x, y)
        >>> forces = [force1, force2, force3]
        >>> u_x, u_y = compute_displacement_field(X, Y, forces, 5000, 0.5)
    """
    u_x_total = np.zeros_like(X)
    u_y_total = np.zeros_like(Y)

    for force in forces:
        u_x, u_y = compute_displacement_from_force(X, Y, force, E, nu)
        u_x_total += u_x
        u_y_total += u_y

    return u_x_total, u_y_total


def create_displacement_grid(field_width, field_height, boundary, sampling_interval):
    """
    创建用于位移场计算的网格
    
    参数:
        field_width (float): 场宽度 (pixel)
        field_height (float): 场高度 (pixel)
        boundary (float): 边界宽度 (pixel)
        sampling_interval (float): 采样间距 (pixel)
    
    返回:
        tuple: (X, Y, x_vec, y_vec)
            X, Y: 网格坐标矩阵
            x_vec, y_vec: 坐标向量
    
    示例:
        >>> X, Y, x_vec, y_vec = create_displacement_grid(500, 500, 40, 10)
        >>> print(f"网格大小: {X.shape}")
    """
    x_vec = np.arange(boundary, field_width - boundary + sampling_interval, sampling_interval)
    y_vec = np.arange(boundary, field_height - boundary + sampling_interval, sampling_interval)
    X, Y = np.meshgrid(x_vec, y_vec)
    return X, Y, x_vec, y_vec


def compute_displacement_magnitude(u_x, u_y):
    """
    计算位移幅值
    
    参数:
        u_x (np.ndarray): x方向位移
        u_y (np.ndarray): y方向位移
    
    返回:
        np.ndarray: 位移幅值 |u| = sqrt(u_x^2 + u_y^2)
    """
    return np.sqrt(u_x**2 + u_y**2)

