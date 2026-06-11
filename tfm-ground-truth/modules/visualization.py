"""牵引力场与位移场可视化（Matplotlib），支持经典和科学两种配色风格。"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib import rcParams
from modules.color_schemes import (
    create_scientific_colormap,
    get_arrow_colors_scientific
)

# 设置中文字体支持
rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
rcParams['axes.unicode_minus'] = False


def plot_traction_field(
    forces,
    field_size,
    ax=None,
    show_arrows=True,
    arrow_density=5,
    style: str = "scientific",
    heatmap_cmap=None,
    arrow_color=None,
    pixel_size_um: float = 1.0,
):
    """
    绘制牵引力场图（带箭头显示力的方向）
    
    参数:
        forces (list): 力的列表,每个力包含position, square_size, Fx, Fy
        field_size (tuple): (width, height) pixel
        ax (matplotlib.axes.Axes): matplotlib轴对象,如果为None则创建新图
        show_arrows (bool): 是否显示箭头,默认True
        arrow_density (int): 箭头密度,每个方向上的箭头数量,默认5
    
    返回:
        matplotlib.axes.Axes: 绘图轴对象
    
    外观要求:
        - 背景: 经典风格为深蓝(jet低值)，科学风格为深蓝(自定义)；无力区域显示为低值背景
        - 力作用区域: 彩色热图 (根据力的大小)
        - 箭头: 经典风格为绿色；科学风格为黄色/科学配色
        - 正方形边界: 白色实线
        - 编号标注: 绿色背景,白色数字

    新增参数:
        style (str): 'classic' 或 'scientific'
            - classic: 经典TFM对比常用风格（热图 jet + 绿箭头）
            - scientific: v1.3 顶刊柔和配色（自定义热图 + 多彩箭头）
        heatmap_cmap: 可选，传入matplotlib cmap对象或cmap名称(str)，覆盖默认
        arrow_color: 可选，覆盖默认箭头颜色
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=(8, 8))
    
    width, height = field_size
    
    # 创建空白画布(黑色背景)
    traction_field = np.zeros((int(height), int(width)))
    
    # 为每个力绘制正方形区域的热图
    for i, force in enumerate(forces, 1):
        x_c, y_c = force['position']
        size = force['square_size']
        half_size = size / 2
        
        # 计算正方形边界
        x_min = int(x_c - half_size)
        x_max = int(x_c + half_size)
        y_min = int(y_c - half_size)
        y_max = int(y_c + half_size)
        
        # 确保边界在场范围内
        x_min = max(0, x_min)
        x_max = min(int(width), x_max)
        y_min = max(0, y_min)
        y_max = min(int(height), y_max)
        
        # 计算牵引应力（Pa）：p = |F| / A
        # forces 中 Fx/Fy 是总力(N)，作用面积由 square_size(pixel) 与 pixel_size_um(μm/pixel) 决定
        Fx = float(force.get("Fx", 0.0))
        Fy = float(force.get("Fy", 0.0))
        F_mag = np.sqrt(Fx**2 + Fy**2)

        length_scale_m = float(pixel_size_um) * 1e-6
        area_m2 = (float(size) * length_scale_m) ** 2 if length_scale_m > 0 else 0.0
        traction_magnitude = (F_mag / area_m2) if area_m2 > 0 else 0.0
        
        # 填充正方形区域
        traction_field[y_min:y_max, x_min:x_max] = traction_magnitude
    
    style_norm = (style or "scientific").strip().lower()
    if heatmap_cmap is None:
        if style_norm == "classic":
            cmap_traction = plt.get_cmap("jet")
        else:
            cmap_traction = create_scientific_colormap("traction")
    else:
        cmap_traction = plt.get_cmap(heatmap_cmap) if isinstance(heatmap_cmap, str) else heatmap_cmap

    # 经典风格需要稳定的0背景（深蓝），因此显式设定vmin/vmax
    vmax = float(np.nanmax(traction_field)) if np.size(traction_field) else 1.0
    if not np.isfinite(vmax) or vmax <= 0:
        vmax = 1.0

    im = ax.imshow(
        traction_field,
        cmap=cmap_traction,
        origin="lower",
        extent=[0, width, 0, height],
        aspect="auto",
        vmin=0.0,
        vmax=vmax,
    )
    
    # 为每个力绘制箭头和标注
    for i, force in enumerate(forces, 1):
        x_c, y_c = force['position']
        size = force['square_size']
        half_size = size / 2
        
        Fx = force.get('Fx', 0)
        Fy = force.get('Fy', 0)
        F_mag = np.sqrt(Fx**2 + Fy**2)
        
        # 绘制正方形边界(白色)
        rect = Rectangle((x_c - half_size, y_c - half_size), size, size,
                         linewidth=2, edgecolor='white', facecolor='none')
        ax.add_patch(rect)
        
        # 在正方形区域内均匀分布箭头
        # 注意：当输入采用“牵引应力(Pa)”并换算为总力(N)时，单个区域的合力可能在1e-7 N量级；
        # 若这里用1e-6 N阈值会导致箭头被误判为“太小而不画”。
        eps_force_n = 1e-12
        if show_arrows and np.isfinite(F_mag) and F_mag > eps_force_n:
            # 计算箭头位置的网格
            arrow_x = np.linspace(x_c - half_size + size/(2*arrow_density), 
                                 x_c + half_size - size/(2*arrow_density), 
                                 arrow_density)
            arrow_y = np.linspace(y_c - half_size + size/(2*arrow_density), 
                                 y_c + half_size - size/(2*arrow_density), 
                                 arrow_density)
            
            # 创建网格点
            Arrow_X, Arrow_Y = np.meshgrid(arrow_x, arrow_y)
            
            # 计算力的方向
            fx_norm = Fx / F_mag if F_mag > 0 else 0
            fy_norm = Fy / F_mag if F_mag > 0 else 0
            
            # 箭头长度（根据正方形大小调整，使箭头更明显）
            arrow_length = size / (arrow_density * 2.5)
            
            # 默认箭头颜色
            if arrow_color is not None:
                arrow_fc = arrow_color
                arrow_ec = arrow_color
            else:
                if style_norm == "classic":
                    arrow_fc = "#00ff00"  # 经典：亮绿色
                    arrow_ec = "#00ff00"
                else:
                    arrow_fc = "yellow"
                    arrow_ec = "yellow"

            # 使用箭头绘制每个位置的力
            for ax_pos, ay_pos in zip(Arrow_X.flatten(), Arrow_Y.flatten()):
                # 计算箭头的终点
                dx = fx_norm * arrow_length
                dy = fy_norm * arrow_length
                
                # 绘制箭头（使用arrow而不是quiver）
                ax.arrow(ax_pos, ay_pos, dx, dy,
                        head_width=arrow_length*0.4, 
                        head_length=arrow_length*0.3,
                        fc=arrow_fc, ec=arrow_ec,
                        linewidth=1.5, alpha=0.9, zorder=5,
                        length_includes_head=True)
        
        # 添加编号标注（放在角落，不在中心）
        # 在左上角显示编号
        label_x = x_c - half_size + 20
        label_y = y_c + half_size - 20
        ax.text(
            label_x,
            label_y,
            str(i),
            ha="center",
            va="center",
            fontsize=16,
            fontweight="bold",
            color="white",
            bbox=dict(boxstyle="circle,pad=0.3", facecolor="green", edgecolor="white", linewidth=2),
            zorder=11,
        )
        
        # 添加力大小标注（转换为μN显示）
        F_mag_uN = F_mag * 1e6  # N → μN
        ax.text(x_c, y_c + half_size + 15, f'{F_mag_uN:.2f} μN', 
               ha='center', va='bottom', fontsize=10, color='white',
               bbox=dict(boxstyle='round,pad=0.3', facecolor='black', alpha=0.7))
    
    # 设置坐标轴和标题
    ax.set_xlabel('x (pixel)', fontsize=12)
    ax.set_ylabel('y (pixel)', fontsize=12)
    ax.set_title('Traction Field', fontsize=14, fontweight='bold')
    ax.set_xlim(0, width)
    ax.set_ylim(0, height)
    
    # 添加色标
    cbar = plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label("Traction Stress (Pa)", fontsize=10)
    
    return ax


def plot_displacement_field(u_x, u_y, X, Y, forces, field_size, 
                            plot_type='magnitude', ax=None, style: str = "scientific", cmap_override=None):
    """
    绘制位移场图
    
    参数:
        u_x, u_y (np.ndarray): 位移场分量
        X, Y (np.ndarray): 网格坐标
        forces (list): 力的列表
        field_size (tuple): (width, height) pixel
        plot_type (str): 绘制类型 'magnitude', 'x', 'y'
        ax (matplotlib.axes.Axes): matplotlib轴对象
    
    返回:
        matplotlib.axes.Axes: 绘图轴对象
    
    外观要求:
        - 背景: 根据位移幅值的彩色热图
        - 色标: 'jet' 或 'RdYlBu_r'
        - 力作用区域边界: 黑色实线
        - 编号标注: 白色背景,黑色数字
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=(8, 8))
    
    width, height = field_size
    
    style_norm = (style or "scientific").strip().lower()

    # 根据绘制类型选择数据和配色
    if plot_type == 'magnitude':
        data = np.sqrt(u_x**2 + u_y**2)
        title = 'Displacement Magnitude'
        cbar_label = 'Displacement (pixel)'
        if cmap_override is not None:
            cmap = plt.get_cmap(cmap_override) if isinstance(cmap_override, str) else cmap_override
        else:
            # 经典：红蓝经典（常见对比图使用jet）
            cmap = plt.get_cmap('jet') if style_norm == "classic" else create_scientific_colormap('magnitude')
    elif plot_type == 'x':
        data = u_x
        title = 'X-Direction Displacement'
        cbar_label = 'u_x (pixel)'
        if cmap_override is not None:
            cmap = plt.get_cmap(cmap_override) if isinstance(cmap_override, str) else cmap_override
        else:
            cmap = plt.get_cmap('RdBu_r') if style_norm == "classic" else create_scientific_colormap('diverging')
    elif plot_type == 'y':
        data = u_y
        title = 'Y-Direction Displacement'
        cbar_label = 'u_y (pixel)'
        if cmap_override is not None:
            cmap = plt.get_cmap(cmap_override) if isinstance(cmap_override, str) else cmap_override
        else:
            cmap = plt.get_cmap('RdBu_r') if style_norm == "classic" else create_scientific_colormap('diverging')
    else:
        raise ValueError(f"未知的绘制类型: {plot_type}")
    
    # 绘制位移场热图
    im = ax.contourf(X, Y, data, levels=50, cmap=cmap)
    
    # 为每个力绘制边界和标注
    for i, force in enumerate(forces, 1):
        x_c, y_c = force['position']
        size = force['square_size']
        half_size = size / 2
        
        # 绘制正方形边界(黑色)
        rect = Rectangle((x_c - half_size, y_c - half_size), size, size,
                         linewidth=1.5, edgecolor='black', facecolor='none')
        ax.add_patch(rect)
        
        # 添加编号标注(白色圆圈)
        circle = plt.Circle((x_c, y_c), radius=15, 
                           color='white', ec='black', linewidth=2, zorder=10)
        ax.add_patch(circle)
        ax.text(x_c, y_c, str(i), ha='center', va='center', 
               fontsize=14, fontweight='bold', color='black', zorder=11)
    
    # 设置坐标轴和标题
    ax.set_xlabel('x (pixel)', fontsize=12)
    ax.set_ylabel('y (pixel)', fontsize=12)
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.set_xlim(0, width)
    ax.set_ylim(0, height)
    ax.set_aspect('equal')
    
    # 添加色标
    cbar = plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label(cbar_label, fontsize=10)
    
    return ax


def plot_displacement_with_vectors(u_x, u_y, X, Y, forces, field_size, 
                                   skip=5, scale=1.0, ax=None, style: str = "scientific"):
    """
    绘制位移场并叠加矢量箭头
    
    参数:
        u_x, u_y (np.ndarray): 位移场分量
        X, Y (np.ndarray): 网格坐标
        forces (list): 力的列表
        field_size (tuple): (width, height) pixel
        skip (int): 箭头间隔,每skip个点绘制一个箭头
        scale (float): 箭头缩放比例
        ax (matplotlib.axes.Axes): matplotlib轴对象
    
    返回:
        matplotlib.axes.Axes: 绘图轴对象
    """
    # 先绘制位移幅值
    style_norm = (style or "scientific").strip().lower()

    ax = plot_displacement_field(
        u_x,
        u_y,
        X,
        Y,
        forces,
        field_size,
        plot_type="magnitude",
        ax=ax,
        style=style_norm,
    )
    
    # 叠加箭头
    vec_color = "#00ff00" if style_norm == "classic" else "white"
    ax.quiver(
        X[::skip, ::skip],
        Y[::skip, ::skip],
        u_x[::skip, ::skip],
        u_y[::skip, ::skip],
        scale=scale,
        color=vec_color,
        alpha=0.75 if style_norm == "classic" else 0.6,
        width=0.003,
    )
    
    ax.set_title('Displacement Field with Vectors', fontsize=14, fontweight='bold')
    
    return ax


def plot_displacement_vectors_only(
    u_x,
    u_y,
    X,
    Y,
    forces,
    field_size,
    skip=5,
    scale=1.0,
    ax=None,
    style: str = "classic",
    vector_color=None,
):
    """
    绘制仅位移矢量的示意图（无热图背景）

    目标外观（经典）:
        - 黑底
        - 绿色箭头
        - 白色方框边界（方框内底色保持黑）

    参数:
        style: 'classic' 或 'scientific'
        vector_color: 可选，覆盖默认矢量颜色
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=(8, 8))

    style_norm = (style or "classic").strip().lower()
    width, height = field_size

    # 背景
    ax.set_facecolor("#000000" if style_norm == "classic" else "#0a0a1a")

    # 方框边界
    for force in forces:
        x_c, y_c = force["position"]
        size = force["square_size"]
        half_size = size / 2
        rect = Rectangle(
            (x_c - half_size, y_c - half_size),
            size,
            size,
            linewidth=2,
            edgecolor="white",
            facecolor="none",
        )
        ax.add_patch(rect)

    # 矢量颜色
    if vector_color is not None:
        vec_color = vector_color
    else:
        vec_color = "#00ff00" if style_norm == "classic" else "white"

    # 绘制位移矢量
    ax.quiver(
        X[::skip, ::skip],
        Y[::skip, ::skip],
        u_x[::skip, ::skip],
        u_y[::skip, ::skip],
        scale=scale,
        color=vec_color,
        alpha=0.75,
        width=0.003,
    )

    ax.set_xlabel("x (pixel)", fontsize=12, color="white")
    ax.set_ylabel("y (pixel)", fontsize=12, color="white")
    ax.set_title("Displacement Field (Vectors)", fontsize=14, fontweight="bold", color="white")
    ax.set_xlim(0, width)
    ax.set_ylim(0, height)
    ax.tick_params(colors="white")

    return ax


def plot_traction_field_arrows_only(
    forces,
    field_size,
    ax=None,
    arrow_density=5,
    style: str = "scientific",
    arrow_color=None,
):
    """
    绘制仅含箭头的牵引力场图（无热图背景）
    
    参数:
        forces (list): 力的列表
        field_size (tuple): (width, height) pixel
        ax (matplotlib.axes.Axes): matplotlib轴对象
        arrow_density (int): 箭头密度
    
    返回:
        matplotlib.axes.Axes: 绘图轴对象
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=(8, 8))
    
    width, height = field_size
    
    style_norm = (style or "scientific").strip().lower()

    # 背景
    if style_norm == "classic":
        ax.set_facecolor("#000000")  # 参考图：纯黑
    else:
        ax.set_facecolor("#0a0a1a")  # 科学配色：深蓝黑
    
    # 为每个力绘制箭头和标注
    for i, force in enumerate(forces, 1):
        x_c, y_c = force['position']
        size = force['square_size']
        half_size = size / 2
        
        Fx = force.get('Fx', 0)
        Fy = force.get('Fy', 0)
        F_mag = np.sqrt(Fx**2 + Fy**2)
        
        # 绘制正方形边界(白色)
        rect = Rectangle((x_c - half_size, y_c - half_size), size, size,
                         linewidth=2, edgecolor='white', facecolor='none')
        ax.add_patch(rect)
        
        # 在正方形区域内均匀分布箭头
        # 同上：降低阈值，避免牵引应力模式下合力很小导致不画箭头
        eps_force_n = 1e-12
        if np.isfinite(F_mag) and F_mag > eps_force_n:
            # 计算箭头位置的网格
            arrow_x = np.linspace(x_c - half_size + size/(2*arrow_density), 
                                 x_c + half_size - size/(2*arrow_density), 
                                 arrow_density)
            arrow_y = np.linspace(y_c - half_size + size/(2*arrow_density), 
                                 y_c + half_size - size/(2*arrow_density), 
                                 arrow_density)
            
            # 创建网格点
            Arrow_X, Arrow_Y = np.meshgrid(arrow_x, arrow_y)
            
            # 计算力的方向
            fx_norm = Fx / F_mag if F_mag > 0 else 0
            fy_norm = Fy / F_mag if F_mag > 0 else 0
            
            # 箭头长度
            arrow_length = size / (arrow_density * 2.5)
            
            # 箭头颜色
            if arrow_color is not None:
                arrow_fc = arrow_color
                arrow_ec = arrow_color
            else:
                if style_norm == "classic":
                    arrow_fc = "#00ff00"  # 参考图：统一绿色箭头
                    arrow_ec = "#00ff00"
                else:
                    arrow_colors = get_arrow_colors_scientific()
                    arrow_fc = arrow_colors[i - 1] if i <= 3 else "white"
                    arrow_ec = arrow_fc
            
            # 使用箭头绘制每个位置的力
            for ax_pos, ay_pos in zip(Arrow_X.flatten(), Arrow_Y.flatten()):
                # 计算箭头的终点
                dx = fx_norm * arrow_length
                dy = fy_norm * arrow_length
                
                # 绘制箭头
                ax.arrow(ax_pos, ay_pos, dx, dy,
                        head_width=arrow_length*0.4, 
                        head_length=arrow_length*0.3,
                        fc=arrow_fc, ec=arrow_ec,
                        linewidth=1.5, alpha=0.9, zorder=5,
                        length_includes_head=True)
        
        # 添加编号标注
        if style_norm == "classic":
            # 参考图：数字更像直接贴在区域中心
            ax.text(
                x_c,
                y_c,
                str(i),
                ha="center",
                va="center",
                fontsize=18,
                fontweight="bold",
                color="white",
                zorder=11,
            )
        else:
            # 科学风格：角落绿色圆圈
            label_x = x_c - half_size + 20
            label_y = y_c + half_size - 20
            ax.text(
                label_x,
                label_y,
                str(i),
                ha="center",
                va="center",
                fontsize=16,
                fontweight="bold",
                color="black",
                bbox=dict(boxstyle="circle,pad=0.3", facecolor="green", edgecolor="white", linewidth=2),
                zorder=11,
            )
        
        # 添加力信息标注（转换为μN显示）
        F_mag_uN = F_mag * 1e6  # N → μN
        ax.text(x_c, y_c + half_size + 15, f'{F_mag_uN:.2f} μN', 
               ha='center', va='bottom', fontsize=10, color='white',
               bbox=dict(boxstyle='round,pad=0.3', facecolor='black', alpha=0.7))
    
    # 设置坐标轴
    ax.set_xlabel("x (pixel)", fontsize=12, color="white")
    ax.set_ylabel("y (pixel)", fontsize=12, color="white")
    ax.set_title("Traction Field (Arrows)", fontsize=14, fontweight="bold", color="white")
    ax.set_xlim(0, width)
    ax.set_ylim(0, height)
    ax.tick_params(colors='white')
    
    return ax


def plot_comparison(
    forces,
    u_x,
    u_y,
    X,
    Y,
    field_size,
    traction_style: str = "scientific",
    displacement_style: str = "scientific",
    traction_arrow_density: int = 5,
):
    """
    并排显示牵引力场和位移场
    
    参数:
        forces (list): 力的列表
        u_x, u_y (np.ndarray): 位移场分量
        X, Y (np.ndarray): 网格坐标
        field_size (tuple): (width, height) pixel
    
    返回:
        matplotlib.figure.Figure: matplotlib图形对象
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))
    
    # 左图: 牵引力场（仅箭头示意）
    plot_traction_field_arrows_only(
        forces,
        field_size,
        ax=ax1,
        arrow_density=traction_arrow_density,
        style=traction_style,
    )
    
    # 右图: 位移场
    plot_displacement_field(
        u_x,
        u_y,
        X,
        Y,
        forces,
        field_size,
        plot_type="magnitude",
        ax=ax2,
        style=displacement_style,
    )
    
    plt.tight_layout()
    
    return fig


def plot_displacement_profile(u_mag, x_vec, y_vec, x_index=None, y_index=None):
    """
    绘制位移剖面图
    
    参数:
        u_mag (np.ndarray): 位移幅值矩阵
        x_vec (np.ndarray): x坐标向量
        y_vec (np.ndarray): y坐标向量
        x_index (int): x方向剖面的索引(固定x,变化y)
        y_index (int): y方向剖面的索引(固定y,变化x)
    
    返回:
        matplotlib.figure.Figure: matplotlib图形对象
    """
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    # x方向剖面 (固定y,变化x)
    if y_index is None:
        y_index = len(y_vec) // 2
    axes[0].plot(x_vec, u_mag[y_index, :], 'b-', linewidth=2)
    axes[0].set_xlabel('x (pixel)', fontsize=12)
    axes[0].set_ylabel('Displacement (pixel)', fontsize=12)
    axes[0].set_title(f'X-Direction Profile (y={y_vec[y_index]:.1f})', 
                     fontsize=14, fontweight='bold')
    axes[0].grid(True, alpha=0.3)
    
    # y方向剖面 (固定x,变化y)
    if x_index is None:
        x_index = len(x_vec) // 2
    axes[1].plot(y_vec, u_mag[:, x_index], 'r-', linewidth=2)
    axes[1].set_xlabel('y (pixel)', fontsize=12)
    axes[1].set_ylabel('Displacement (pixel)', fontsize=12)
    axes[1].set_title(f'Y-Direction Profile (x={x_vec[x_index]:.1f})', 
                     fontsize=14, fontweight='bold')
    axes[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    return fig

