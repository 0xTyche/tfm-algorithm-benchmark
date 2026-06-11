"""科学出版级配色方案（顶刊常用色板与自定义 colormap）。"""

import numpy as np
from matplotlib.colors import LinearSegmentedColormap, ListedColormap
import matplotlib.pyplot as plt


# 顶刊常用配色（用户提供）
JOURNAL_COLORS = {
    'color1': {'hex': '#DCA7EB', 'rgb': (220, 167, 235), 'name': 'Lavender'},
    'color2': {'hex': '#A0D0D0', 'rgb': (160, 208, 208), 'name': 'Cyan'},
    'color3': {'hex': '#EAE936', 'rgb': (234, 233, 54), 'name': 'Yellow'},
    'color4': {'hex': '#B7F5DE', 'rgb': (183, 245, 222), 'name': 'Mint'},
    'color5': {'hex': '#D5AABE', 'rgb': (213, 170, 190), 'name': 'Rose'},
    'color6': {'hex': '#A7C0DF', 'rgb': (167, 192, 223), 'name': 'Sky Blue'},
}


def create_scientific_colormap(name='traction', n_bins=256):
    """
    创建科学级配色方案
    
    参数:
        name (str): 配色方案名称 'traction', 'displacement', 'diverging'
        n_bins (int): 颜色分级数
    
    返回:
        matplotlib.colors.LinearSegmentedColormap: 配色方案对象
    """
    if name == 'traction':
        # 牵引力场配色：深色 → 浅蓝 → 薄荷绿 → 黄色
        # 适合从低到高的单向数据
        colors = [
            (0.0, 0.0, 0.1),      # 深蓝（几乎黑色）
            (0.2, 0.3, 0.5),      # 深蓝
            (160/255, 208/255, 208/255),  # 青色 (color2)
            (183/255, 245/255, 222/255),  # 薄荷绿 (color4)
            (234/255, 233/255, 54/255),   # 黄色 (color3)
        ]
        cmap = LinearSegmentedColormap.from_list('traction_scientific', colors, N=n_bins)
        
    elif name == 'displacement':
        # 位移场配色：蓝 → 白 → 红（发散型）
        # 适合有正负的数据
        colors = [
            (167/255, 192/255, 223/255),  # 天蓝 (color6)
            (160/255, 208/255, 208/255),  # 青色 (color2)
            (183/255, 245/255, 222/255),  # 薄荷绿 (color4)
            (234/255, 233/255, 54/255),   # 黄色 (color3)
            (220/255, 167/255, 235/255),  # 淡紫 (color1)
            (213/255, 170/255, 190/255),  # 玫瑰 (color5)
        ]
        cmap = LinearSegmentedColormap.from_list('displacement_scientific', colors, N=n_bins)
        
    elif name == 'magnitude':
        # 位移幅值配色：深蓝 → 薄荷 → 黄 → 玫瑰
        # 适合幅值数据（只有正值）
        colors = [
            (0.05, 0.05, 0.15),   # 深蓝
            (167/255, 192/255, 223/255),  # 天蓝 (color6)
            (183/255, 245/255, 222/255),  # 薄荷绿 (color4)
            (234/255, 233/255, 54/255),   # 黄色 (color3)
            (220/255, 167/255, 235/255),  # 淡紫 (color1)
        ]
        cmap = LinearSegmentedColormap.from_list('magnitude_scientific', colors, N=n_bins)
        
    elif name == 'diverging':
        # 发散配色：蓝 → 白 → 玫瑰红
        # 适合有正负中心值的数据
        colors = [
            (167/255, 192/255, 223/255),  # 天蓝 (color6)
            (183/255, 245/255, 222/255),  # 薄荷绿 (color4)
            (1.0, 1.0, 1.0),              # 白色
            (220/255, 167/255, 235/255),  # 淡紫 (color1)
            (213/255, 170/255, 190/255),  # 玫瑰 (color5)
        ]
        cmap = LinearSegmentedColormap.from_list('diverging_scientific', colors, N=n_bins)
    
    else:
        # 默认使用magnitude配色
        return create_scientific_colormap('magnitude', n_bins)
    
    return cmap


def get_arrow_colors_scientific():
    """
    获取箭头的科学配色
    
    返回:
        list: 三个力对应的箭头颜色（HEX格式）
    """
    return [
        '#A7C0DF',  # 力1：天蓝 (color6)
        '#B7F5DE',  # 力2：薄荷绿 (color4)
        '#EAE936',  # 力3：黄色 (color3)
    ]


def get_discrete_colors(n_colors=6):
    """
    获取离散的科学配色
    
    参数:
        n_colors (int): 需要的颜色数量
    
    返回:
        list: HEX颜色列表
    """
    all_colors = [
        '#DCA7EB',  # color1: 淡紫
        '#A0D0D0',  # color2: 青色
        '#EAE936',  # color3: 黄色
        '#B7F5DE',  # color4: 薄荷绿
        '#D5AABE',  # color5: 玫瑰
        '#A7C0DF',  # color6: 天蓝
    ]
    
    return all_colors[:n_colors]


def demo_colormaps():
    """
    演示所有配色方案
    """
    fig, axes = plt.subplots(4, 1, figsize=(10, 8))
    
    # 创建示例数据
    x = np.linspace(0, 10, 100)
    y = np.linspace(0, 10, 100)
    X, Y = np.meshgrid(x, y)
    
    # 单向数据（牵引力场）
    Z1 = np.exp(-((X-5)**2 + (Y-5)**2) / 5)
    
    # 发散数据（位移）
    Z2 = np.sin(X) * np.cos(Y)
    
    # 配色方案1: Traction
    cmap1 = create_scientific_colormap('traction')
    im1 = axes[0].contourf(X, Y, Z1, levels=20, cmap=cmap1)
    axes[0].set_title('Traction Field Colormap', fontsize=12, fontweight='bold')
    plt.colorbar(im1, ax=axes[0])
    
    # 配色方案2: Magnitude
    cmap2 = create_scientific_colormap('magnitude')
    im2 = axes[1].contourf(X, Y, Z1, levels=20, cmap=cmap2)
    axes[1].set_title('Magnitude Colormap', fontsize=12, fontweight='bold')
    plt.colorbar(im2, ax=axes[1])
    
    # 配色方案3: Displacement
    cmap3 = create_scientific_colormap('displacement')
    im3 = axes[2].contourf(X, Y, Z2, levels=20, cmap=cmap3)
    axes[2].set_title('Displacement Colormap', fontsize=12, fontweight='bold')
    plt.colorbar(im3, ax=axes[2])
    
    # 配色方案4: Diverging
    cmap4 = create_scientific_colormap('diverging')
    im4 = axes[3].contourf(X, Y, Z2, levels=20, cmap=cmap4)
    axes[3].set_title('Diverging Colormap', fontsize=12, fontweight='bold')
    plt.colorbar(im4, ax=axes[3])
    
    plt.tight_layout()
    plt.savefig('colormap_demo.png', dpi=150, bbox_inches='tight')
    print("配色演示已保存: colormap_demo.png")
    plt.show()


if __name__ == "__main__":
    print("生成配色方案演示...")
    demo_colormaps()

