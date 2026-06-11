"""合成荧光微珠图像生成：参考帧与变形帧（16-bit TIFF，物理 PSF 模型）。"""

import numpy as np
from scipy.ndimage import gaussian_filter
from scipy.interpolate import RegularGridInterpolator


def generate_bead_positions(field_width, field_height, num_beads, 
                            boundary=40, min_distance=10, seed=None):
    """
    在场内随机生成荧光珠位置
    
    参数:
        field_width (float): 场宽度 (pixel)
        field_height (float): 场高度 (pixel)
        num_beads (int): 荧光珠数量
        boundary (float): 边界宽度，避免在边缘生成 (pixel)
        min_distance (float): 荧光珠之间的最小距离 (pixel)
        seed (int): 随机种子，用于可重复性
    
    返回:
        np.ndarray: N×2数组，每行是[x, y]坐标
    
    示例:
        >>> beads = generate_bead_positions(500, 500, 100)
        >>> print(beads.shape)
        (100, 2)
    """
    if seed is not None:
        np.random.seed(seed)
    
    beads = []
    attempts = 0
    max_attempts = num_beads * 100
    
    while len(beads) < num_beads and attempts < max_attempts:
        # 随机生成候选位置
        x = np.random.uniform(boundary, field_width - boundary)
        y = np.random.uniform(boundary, field_height - boundary)
        
        # 检查是否与已有荧光珠距离足够
        if len(beads) == 0:
            beads.append([x, y])
        else:
            beads_array = np.array(beads)
            distances = np.sqrt((beads_array[:, 0] - x)**2 + (beads_array[:, 1] - y)**2)
            if np.all(distances >= min_distance):
                beads.append([x, y])
        
        attempts += 1
    
    if len(beads) < num_beads:
        print(f"警告: 只生成了 {len(beads)} 个荧光珠（目标 {num_beads} 个）")
    
    return np.array(beads)


def create_gaussian_spot(x, y, image_shape, sigma=2.0, intensity=1.0):
    """
    在指定位置创建高斯光斑
    
    参数:
        x (float): x坐标 (pixel)
        y (float): y坐标 (pixel)
        image_shape (tuple): 图像尺寸 (height, width)
        sigma (float): 高斯标准差 (pixel)
        intensity (float): 光斑强度
    
    返回:
        np.ndarray: 包含高斯光斑的图像
    
    注意:
        只在光斑附近的局部区域计算，提高效率
    """
    height, width = image_shape
    image = np.zeros(image_shape, dtype=np.float32)
    
    # 计算局部区域（3*sigma范围）
    radius = int(3 * sigma) + 1
    x_min = max(0, int(x) - radius)
    x_max = min(width, int(x) + radius + 1)
    y_min = max(0, int(y) - radius)
    y_max = min(height, int(y) + radius + 1)
    
    # 创建局部网格
    xx, yy = np.meshgrid(np.arange(x_min, x_max), np.arange(y_min, y_max))
    
    # 计算高斯函数
    gaussian = intensity * np.exp(-((xx - x)**2 + (yy - y)**2) / (2 * sigma**2))
    
    # 添加到图像
    image[y_min:y_max, x_min:x_max] = gaussian
    
    return image


def generate_reference_image(bead_positions, field_width, field_height,
                             sigma=2.0, intensity=1000.0, noise_level=50.0,
                             background=100.0,
                             noise_mode: str = "independent_gaussian",
                             random_seed=None):
    """
    生成参考图像（未变形）
    
    参数:
        bead_positions (np.ndarray): N×2荧光珠位置数组
        field_width (float): 图像宽度 (pixel)
        field_height (float): 图像高度 (pixel)
        sigma (float): 高斯光斑标准差 (pixel)
        intensity (float): 荧光珠亮度
        noise_level (float): 噪声标准差
        background (float): 背景亮度
    
    返回:
        np.ndarray: 参考图像 (uint16)
    
    示例:
        >>> beads = generate_bead_positions(500, 500, 100)
        >>> ref_img = generate_reference_image(beads, 500, 500)
        >>> print(ref_img.shape, ref_img.dtype)
        (500, 500) uint16
    """
    if random_seed is not None:
        np.random.seed(random_seed)

    # 创建空白图像
    image = np.ones((int(field_height), int(field_width)), dtype=np.float32) * background
    
    # 添加每个荧光珠
    print(f"生成参考图像: 添加 {len(bead_positions)} 个荧光珠...")
    for i, (x, y) in enumerate(bead_positions):
        if i % 100 == 0:
            print(f"  进度: {i}/{len(bead_positions)}")
        spot = create_gaussian_spot(x, y, image.shape, sigma, intensity)
        image += spot
    
    # 添加噪声
    noise_mode_norm = (noise_mode or "independent_gaussian").strip().lower()
    if noise_level and noise_level > 0:
        if noise_mode_norm in ("independent_gaussian", "gaussian"):
            noise = np.random.normal(0, noise_level, image.shape)
            image += noise
        elif noise_mode_norm in ("none", "off"):
            pass
        else:
            noise = np.random.normal(0, noise_level, image.shape)
            image += noise
    
    # 限制范围并转换为uint16
    image = np.clip(image, 0, 65535)
    image = image.astype(np.uint16)
    
    print(f"参考图像生成完成: {image.shape}, 范围[{image.min()}, {image.max()}]")
    
    return image


def interpolate_displacement(bead_positions, X, Y, u_x, u_y):
    """
    在荧光珠位置插值位移
    
    参数:
        bead_positions (np.ndarray): N×2荧光珠位置数组
        X (np.ndarray): 位移场的x坐标网格
        Y (np.ndarray): 位移场的y坐标网格
        u_x (np.ndarray): x方向位移场
        u_y (np.ndarray): y方向位移场
    
    返回:
        tuple: (ux_interp, uy_interp) 插值后的位移向量
    
    注意:
        使用双线性插值
    """
    # 创建插值函数
    # 注意：RegularGridInterpolator需要(行, 列)顺序，即(y, x)
    x_vec = X[0, :]  # 第一行就是x坐标
    y_vec = Y[:, 0]  # 第一列就是y坐标
    
    # 创建插值器
    interp_ux = RegularGridInterpolator((y_vec, x_vec), u_x, 
                                       bounds_error=False, fill_value=0)
    interp_uy = RegularGridInterpolator((y_vec, x_vec), u_y, 
                                       bounds_error=False, fill_value=0)
    
    # 插值（注意顺序：(y, x)）
    points = bead_positions[:, [1, 0]]  # 交换为(y, x)顺序
    ux_interp = interp_ux(points)
    uy_interp = interp_uy(points)
    
    return ux_interp, uy_interp


def generate_deformed_image(bead_positions, X, Y, u_x, u_y, 
                           field_width, field_height,
                           sigma=2.0, intensity=1000.0, noise_level=50.0,
                           background=100.0,
                           displacement_scale=1.0,
                           noise_mode: str = "independent_gaussian",
                           random_seed=None):
    """
    生成变形图像（荧光珠移动后）
    
    参数:
        bead_positions (np.ndarray): N×2原始荧光珠位置
        X, Y (np.ndarray): 位移场网格坐标
        u_x, u_y (np.ndarray): 位移场分量
        field_width (float): 图像宽度 (pixel)
        field_height (float): 图像高度 (pixel)
        sigma (float): 高斯光斑标准差 (pixel)
        intensity (float): 荧光珠亮度
        noise_level (float): 噪声标准差
        background (float): 背景亮度
    
    返回:
        tuple: (deformed_image, displaced_positions)
            deformed_image: 变形图像 (uint16)
            displaced_positions: 移动后的荧光珠位置
    
    示例:
        >>> ref_beads = generate_bead_positions(500, 500, 100)
        >>> def_img, def_beads = generate_deformed_image(
        ...     ref_beads, X, Y, u_x, u_y, 500, 500)
    """
    if random_seed is not None:
        np.random.seed(random_seed)

    # 插值位移
    print(f"插值位移场到荧光珠位置...")
    ux_at_beads, uy_at_beads = interpolate_displacement(bead_positions, X, Y, u_x, u_y)

    # 位移缩放：用于确保PIV可追踪（典型目标 0.1-2 pixel）
    try:
        displacement_scale_val = float(displacement_scale)
    except Exception:
        displacement_scale_val = 1.0
    if not np.isfinite(displacement_scale_val) or displacement_scale_val <= 0:
        displacement_scale_val = 1.0
    if displacement_scale_val != 1.0:
        ux_at_beads = ux_at_beads * displacement_scale_val
        uy_at_beads = uy_at_beads * displacement_scale_val
    
    # 计算移动后的位置
    displaced_positions = bead_positions.copy()
    displaced_positions[:, 0] += ux_at_beads  # x方向位移
    displaced_positions[:, 1] += uy_at_beads  # y方向位移
    
    # 统计位移信息
    displacement_mag = np.sqrt(ux_at_beads**2 + uy_at_beads**2)
    print(f"位移统计:")
    print(f"  平均位移: {np.mean(displacement_mag):.6f} pixel")
    print(f"  最大位移: {np.max(displacement_mag):.6f} pixel")
    print(f"  最小位移: {np.min(displacement_mag):.6f} pixel")
    
    # 创建空白图像
    image = np.ones((int(field_height), int(field_width)), dtype=np.float32) * background
    
    # 添加每个荧光珠（在新位置）
    print(f"生成变形图像: 添加 {len(displaced_positions)} 个荧光珠...")
    valid_count = 0
    for i, (x, y) in enumerate(displaced_positions):
        if i % 100 == 0:
            print(f"  进度: {i}/{len(displaced_positions)}")
        
        # 检查是否在图像范围内
        if 0 <= x < field_width and 0 <= y < field_height:
            spot = create_gaussian_spot(x, y, image.shape, sigma, intensity)
            image += spot
            valid_count += 1
    
    print(f"  有效荧光珠: {valid_count}/{len(displaced_positions)}")
    
    # 添加高斯噪声
    noise_mode_norm = (noise_mode or "independent_gaussian").strip().lower()
    if noise_level and noise_level > 0:
        if noise_mode_norm in ("independent_gaussian", "gaussian"):
            noise = np.random.normal(0, noise_level, image.shape)
            image += noise
        elif noise_mode_norm in ("none", "off"):
            pass
        else:
            # 回退：独立高斯噪声
            noise = np.random.normal(0, noise_level, image.shape)
            image += noise
    
    # 限制范围并转换为uint16
    image = np.clip(image, 0, 65535)
    image = image.astype(np.uint16)
    
    print(f"变形图像生成完成: {image.shape}, 范围[{image.min()}, {image.max()}]")
    
    return image, displaced_positions


def calculate_psf_sigma(wavelength, numerical_aperture, pixel_size):
    """
    根据光学参数计算点扩散函数(PSF)的sigma值
    
    参数:
        wavelength (float): 波长 (nm)
        numerical_aperture (float): 数值孔径
        pixel_size (float): 像素大小 (um/pixel)
    
    返回:
        float: PSF的sigma值 (pixel)
    
    理论基础:
        艾里斑半径 r = 0.61 * λ / NA
        高斯近似: σ ≈ 0.21 * λ / NA (转换为pixel)
    """
    # 艾里斑半径 (nm)
    airy_radius_nm = 0.61 * wavelength / numerical_aperture
    
    # 转换为um
    airy_radius_um = airy_radius_nm / 1000
    
    # 高斯sigma (约为艾里斑半径的0.42倍)
    sigma_um = airy_radius_um * 0.42
    
    # 转换为pixel
    sigma_pixel = sigma_um / pixel_size
    
    return sigma_pixel


def apply_photobleaching(image, bleach_factor=0.95):
    """
    应用光漂白效应
    
    参数:
        image (np.ndarray): 输入图像
        bleach_factor (float): 漂白因子 (0-1)，1表示无漂白
    
    返回:
        np.ndarray: 应用漂白后的图像
    """
    return (image * bleach_factor).astype(image.dtype)


def apply_shot_noise(image, photon_conversion_factor=1.0):
    """
    应用散粒噪声(Poisson噪声)
    
    参数:
        image (np.ndarray): 输入图像
        photon_conversion_factor (float): 光子转换因子
    
    返回:
        np.ndarray: 添加散粒噪声后的图像
    """
    # 转换为光子数
    photons = image / photon_conversion_factor
    
    # 应用Poisson噪声
    noisy_photons = np.random.poisson(photons)
    
    # 转换回强度值
    noisy_image = noisy_photons * photon_conversion_factor
    
    return noisy_image.astype(image.dtype)


def save_image_pair_with_metadata(reference_image, deformed_image, 
                                  metadata_dict,
                                  ref_filename='reference.tif', 
                                  def_filename='deformed.tif',
                                  compression: str | None = "deflate",
                                  imagej: bool = True):
    """
    保存参考图像和变形图像为TIF格式（包含完整元数据）
    
    参数:
        reference_image (np.ndarray): 参考图像
        deformed_image (np.ndarray): 变形图像
        metadata_dict (dict): 元数据字典
        ref_filename (str): 参考图像文件名
        def_filename (str): 变形图像文件名
    
    返回:
        tuple: (ref_filename, def_filename)
    """
    import tifffile
    from datetime import datetime
    
    # 准备ImageJ兼容的元数据
    imagej_metadata = {
        'Info': f"""
TFM Synthetic Image Generator
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

=== Microscope Parameters ===
Sampling Mode: {metadata_dict.get('sampling_mode', 'N/A')}
Fluorophore: {metadata_dict.get('fluorophore', 'N/A')}
Excitation Wavelength: {metadata_dict.get('excitation_wavelength', 'N/A')} nm
Emission Wavelength: {metadata_dict.get('emission_wavelength', 'N/A')} nm
Exposure Time: {metadata_dict.get('exposure_time', 'N/A')} ms
Pixel Size: {metadata_dict.get('pixel_size', 'N/A')} um/pixel
Numerical Aperture: {metadata_dict.get('numerical_aperture', 'N/A')}
Camera Bit Depth: {metadata_dict.get('bit_depth', 'N/A')} bit

=== Image Parameters ===
Bead Count: {metadata_dict.get('bead_count', 'N/A')}
PSF Sigma: {metadata_dict.get('psf_sigma', 'N/A'):.3f} pixel
Bead Intensity: {metadata_dict.get('bead_intensity', 'N/A')}
Noise Level: {metadata_dict.get('noise_level', 'N/A')}
Background: {metadata_dict.get('background', 'N/A')}

=== Displacement Field ===
Max Displacement: {metadata_dict.get('max_displacement', 'N/A')} pixel
Mean Displacement: {metadata_dict.get('mean_displacement', 'N/A')} pixel
""",
        'unit': 'um',
        'spacing': metadata_dict.get('pixel_size', 1.0)
    }
    
    # OME-TIFF元数据
    ome_metadata = {
        'axes': 'YX',
        'PhysicalSizeX': metadata_dict.get('pixel_size', 1.0),
        'PhysicalSizeXUnit': 'µm',
        'PhysicalSizeY': metadata_dict.get('pixel_size', 1.0),
        'PhysicalSizeYUnit': 'µm',
    }
    
    # 保存参考图像
    ref_metadata = metadata_dict.copy()
    ref_metadata['image_type'] = 'Reference'
    ref_metadata['time_point'] = 0

    if imagej:
        tifffile.imwrite(
            ref_filename,
            reference_image,
            imagej=True,
            resolution=(1.0/metadata_dict.get('pixel_size', 1.0),
                       1.0/metadata_dict.get('pixel_size', 1.0)),
            metadata=imagej_metadata,
            photometric='minisblack',
            compression=compression
        )
    else:
        # 兼容模式：最朴素的16-bit灰度TIFF（避免ImageJ元数据/压缩导致部分旧软件读入异常）
        tifffile.imwrite(
            ref_filename,
            reference_image,
            photometric='minisblack',
            compression=compression
        )
    print(f"✓ 参考图像已保存: {ref_filename}")
    
    # 保存变形图像
    def_metadata = metadata_dict.copy()
    def_metadata['image_type'] = 'Deformed'
    def_metadata['time_point'] = metadata_dict.get('time_interval', 1.0)
    
    def_imagej_metadata = imagej_metadata.copy()
    def_imagej_metadata['Info'] = imagej_metadata['Info'].replace('Reference', 'Deformed')
    
    if imagej:
        tifffile.imwrite(
            def_filename,
            deformed_image,
            imagej=True,
            resolution=(1.0/metadata_dict.get('pixel_size', 1.0),
                       1.0/metadata_dict.get('pixel_size', 1.0)),
            metadata=def_imagej_metadata,
            photometric='minisblack',
            compression=compression
        )
    else:
        tifffile.imwrite(
            def_filename,
            deformed_image,
            photometric='minisblack',
            compression=compression
        )
    print(f"✓ 变形图像已保存: {def_filename}")
    
    return ref_filename, def_filename


def save_image_pair(reference_image, deformed_image, 
                   ref_filename='reference.tif', 
                   def_filename='deformed.tif'):
    """
    保存参考图像和变形图像为TIF格式（简化版，向后兼容）
    
    参数:
        reference_image (np.ndarray): 参考图像
        deformed_image (np.ndarray): 变形图像
        ref_filename (str): 参考图像文件名
        def_filename (str): 变形图像文件名
    
    返回:
        tuple: (ref_filename, def_filename)
    """
    import tifffile
    
    # 保存参考图像
    tifffile.imwrite(ref_filename, reference_image, photometric='minisblack')
    print(f"✓ 参考图像已保存: {ref_filename}")
    
    # 保存变形图像
    tifffile.imwrite(def_filename, deformed_image, photometric='minisblack')
    print(f"✓ 变形图像已保存: {def_filename}")
    
    return ref_filename, def_filename

