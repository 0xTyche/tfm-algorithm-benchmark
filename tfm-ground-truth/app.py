import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import time
from datetime import datetime

# 图像显示尺寸（避免前端裁切）
FIGSIZE_SINGLE = (6.0, 6.0)
FIGSIZE_COMPARE = (10.0, 4.8)


def show_fig_centered(fig, center_ratio: int = 3):
    """
    在页面中居中显示图像，并限制最大显示宽度。
    Streamlit 全宽渲染时，正方形图会变得过高导致“一屏只显示一半”。
    """
    left, center, right = st.columns([1, center_ratio, 1])
    with center:
        st.pyplot(fig, use_container_width=True)

# 导入自定义模块
from modules.force_balance import (
    calculate_force_components,
    calculate_third_force,
    verify_equilibrium,
    format_equilibrium_result,
    find_balanced_position_for_force3
)
from modules.displacement import (
    create_displacement_grid,
    compute_displacement_field_si,
    compute_displacement_magnitude
)
from modules.visualization import (
    plot_traction_field,
    plot_traction_field_arrows_only,
    plot_displacement_field,
    plot_displacement_with_vectors,
    plot_displacement_vectors_only,
    plot_comparison,
    plot_displacement_profile
)
from modules.data_export import (
    export_forces_to_mat,
    export_displacement_to_mat,
    prepare_displacement_export,
    export_displacement_full
)
from modules.image_generator import (
    generate_bead_positions,
    generate_reference_image,
    generate_deformed_image,
    save_image_pair_with_metadata,
    calculate_psf_sigma,
    apply_shot_noise as apply_shot_noise_fn
)
from modules.algorithm_inputs import build_algorithm_inputs_zip, PyTFMParams
from utils.helpers import validate_inputs, check_squares_overlap


# 页面配置
st.set_page_config(
    page_title="BIS方法牵引力-位移场计算器",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 标题
st.title("🔬 BIS方法牵引力-位移场计算器")

# 添加单位说明
with st.expander("📐 单位系统说明（重要！请阅读）"):
    st.markdown("""
    ### 单位约定
    
    本程序采用以下单位系统：
    
    | 物理量 | 单位 | 说明 |
    |--------|------|------|
    | **集中力 F** | **N**（牛顿） | 作用在点或小区域的力 |
    | **位置坐标** | pixel ≡ μm | **假设 1 pixel = 1 μm** |
    | **正方形边长** | pixel ≡ μm | 力的作用区域大小 |
    | **杨氏模量 E** | kPa（输入）→ Pa（计算） | 材料弹性模量 |
    | **牵引应力 p** | Pa ≡ N/μm² ≡ N/pixel² | 单位面积上的力 |
    | **位移 u** | pixel ≡ μm | 基底变形量 |
    
    ### 关键假设
    
    ⚠️ **1 pixel = 1 μm = 10⁻⁶ m**
    
    这意味着：
    - 位置 (250, 340) pixel = (250, 340) μm
    - 面积 80×80 pixel² = 6400 μm²
    - 牵引应力 p = F/A = N/μm² = Pa（单位自动匹配）
    
    ### 单位换算示例
    
    **输入**：
    - 集中力 F₁ = 18 N
    - 正方形边长 = 80 pixel = 80 μm
    - 杨氏模量 E = 5 kPa = 5000 Pa
    
    **计算**：
    - 面积 A = 80² = 6400 pixel² = 6400 μm²
    - 牵引应力 p = 18 N / 6400 μm² = 0.0028125 N/μm² = 2812.5 Pa
    - 预期位移量级: 10⁻³ - 10⁻¹ μm ≡ 10⁻³ - 10⁻¹ pixel
    
    ### ✅ 正确性验证
    
    - 杨氏模量转换：5 kPa × 1000 = 5000 Pa ✓
    - 力矩单位：N·pixel ≡ N·μm ≡ 10⁻⁶ N·m ✓
    - 位移单位：pixel ≡ μm ✓
    
    所有计算都在SI单位系统下进行（假设pixel=μm）。
    """)

st.markdown("---")

# 默认参数（v1.4修正：增大力，减小E，产生PIV可追踪的位移）
DEFAULT_PARAMS = {
    # 材料参数
    'E': 5.0,           # kPa（贴近常见软凝胶量级；若位移太小可再减小）
    'nu': 0.5,
    'pixel_size_um': 1.0,  # μm/pixel（贴近“像素≈μm”的论文表述；相机真实值可改为0.108等）
    
    # 场设置
    'field_width': 500.0,   # pixel ≡ μm
    'field_height': 500.0,
    'boundary': 40.0,
    'sampling_interval': 10.0,
    
    # 力输入（默认采用：牵引应力 Pa，贴近论文）
    'force_input_mode': 'traction_stress',
    'force1_traction_pa': 18.0,     # Pa（均匀牵引应力）
    'force1_angle': 135.0,         # 度
    'force1_x': 150.0,
    'force1_y': 190.0,
    'force1_size': 80.0,
    
    'force2_traction_pa': 18.0,     # Pa
    'force2_angle': 45.0,
    'force2_x': 360.0,
    'force2_y': 220.0,
    'force2_size': 80.0,
    
    # 力3
    'force3_x': 260.0,
    'force3_y': 340.0,
    'force3_size': 70.0,
}

# 初始化session state
if 'calculated' not in st.session_state:
    st.session_state.calculated = False
if 'force3' not in st.session_state:
    st.session_state.force3 = None
if 'displacement_computed' not in st.session_state:
    st.session_state.displacement_computed = False

# ========== 侧边栏: 参数输入 ==========
st.sidebar.header("📋 参数设置")

# 1. 材料参数
st.sidebar.subheader("1. 材料参数")
E_kPa = st.sidebar.number_input("杨氏模量 E (kPa)", 
                                 min_value=0.1, max_value=1000.0, 
                                 value=DEFAULT_PARAMS['E'], step=0.1)
nu = st.sidebar.number_input("泊松比 ν", 
                             min_value=-1.0, max_value=0.5, 
                             value=DEFAULT_PARAMS['nu'], step=0.01)

pixel_size_um = st.sidebar.number_input(
    "像素尺寸 (μm/pixel)",
    min_value=0.001,
    max_value=10.0,
    value=DEFAULT_PARAMS["pixel_size_um"],
    step=0.001,
    format="%.3f",
    help="用于把“牵引应力Pa + 区域面积”换算成总力(N)，并用于SI单位位移求解。",
)

# 2. 场设置
st.sidebar.subheader("2. 场设置")
field_width = st.sidebar.number_input("场宽度 (pixel)", 
                                      min_value=100.0, max_value=2000.0, 
                                      value=DEFAULT_PARAMS['field_width'], step=10.0)
field_height = st.sidebar.number_input("场高度 (pixel)", 
                                       min_value=100.0, max_value=2000.0, 
                                       value=DEFAULT_PARAMS['field_height'], step=10.0)
boundary = st.sidebar.number_input("边界 (pixel)", 
                                   min_value=0.0, max_value=100.0, 
                                   value=DEFAULT_PARAMS['boundary'], step=5.0)
sampling_interval = st.sidebar.number_input("采样间距 (pixel)", 
                                            min_value=1.0, max_value=50.0, 
                                            value=DEFAULT_PARAMS['sampling_interval'], step=1.0)

# 3. 力1 (已知)
st.sidebar.subheader("3. 力1 (已知)")
force_input_mode = st.sidebar.radio(
    "力输入类型",
    options=["牵引应力 (Pa)", "集中力 (μN)"],
    index=0 if DEFAULT_PARAMS.get("force_input_mode") == "traction_stress" else 1,
    help="论文常见写法是给每个区域的均匀牵引应力(Pa)。集中力模式用于兼容旧用法。",
)

if force_input_mode == "牵引应力 (Pa)":
    force1_traction_pa = st.sidebar.number_input(
        "牵引应力大小 (Pa)",
        min_value=0.0,
        value=DEFAULT_PARAMS["force1_traction_pa"],
        step=0.1,
        key="f1_trac",
    )
    force1_magnitude = None
else:
    force1_magnitude = st.sidebar.number_input(
        "集中力大小 (μN)",
        min_value=0.0,
        value=float(DEFAULT_PARAMS.get("force1_magnitude", 2000.0)),
        step=1.0,
        key="f1_mag",
    )
    force1_traction_pa = None
force1_angle = st.sidebar.number_input("方向 (度)", 
                                       min_value=-180.0, max_value=180.0, 
                                       value=DEFAULT_PARAMS['force1_angle'], 
                                       step=1.0, key='f1_angle')
force1_x = st.sidebar.number_input("位置 x (pixel)", 
                                   value=DEFAULT_PARAMS['force1_x'], 
                                   step=1.0, key='f1_x')
force1_y = st.sidebar.number_input("位置 y (pixel)", 
                                   value=DEFAULT_PARAMS['force1_y'], 
                                   step=1.0, key='f1_y')
force1_size = st.sidebar.number_input("正方形边长 (pixel)", 
                                      min_value=1.0, 
                                      value=DEFAULT_PARAMS['force1_size'], 
                                      step=1.0, key='f1_size')

# 4. 力2 (已知)
st.sidebar.subheader("4. 力2 (已知)")
if force_input_mode == "牵引应力 (Pa)":
    force2_traction_pa = st.sidebar.number_input(
        "牵引应力大小 (Pa)",
        min_value=0.0,
        value=DEFAULT_PARAMS["force2_traction_pa"],
        step=0.1,
        key="f2_trac",
    )
    force2_magnitude = None
else:
    force2_magnitude = st.sidebar.number_input(
        "集中力大小 (μN)",
        min_value=0.0,
        value=float(DEFAULT_PARAMS.get("force2_magnitude", 2000.0)),
        step=1.0,
        key="f2_mag",
    )
    force2_traction_pa = None
force2_angle = st.sidebar.number_input("方向 (度)", 
                                       min_value=-180.0, max_value=180.0, 
                                       value=DEFAULT_PARAMS['force2_angle'], 
                                       step=1.0, key='f2_angle')
force2_x = st.sidebar.number_input("位置 x (pixel)", 
                                   value=DEFAULT_PARAMS['force2_x'], 
                                   step=1.0, key='f2_x')
force2_y = st.sidebar.number_input("位置 y (pixel)", 
                                   value=DEFAULT_PARAMS['force2_y'], 
                                   step=1.0, key='f2_y')
force2_size = st.sidebar.number_input("正方形边长 (pixel)", 
                                      min_value=1.0, 
                                      value=DEFAULT_PARAMS['force2_size'], 
                                      step=1.0, key='f2_size')

# 5. 力3 (待求) - 自动计算以满足力矩平衡
st.sidebar.subheader("5. 力3 (待求)")

st.sidebar.info("💡 系统将自动计算F3的位置(x)、大小和方向，以严格满足力和力矩平衡")

# 用户只需要指定y坐标和正方形大小
force3_y = st.sidebar.number_input("位置 y (pixel) - 可指定", 
                                   value=DEFAULT_PARAMS['force3_y'], 
                                   step=1.0, key='f3_y',
                                   help="指定F3的y坐标，x坐标将自动计算以满足力矩平衡")

force3_size = st.sidebar.number_input("正方形边长 (pixel)", 
                                      min_value=1.0, 
                                      value=DEFAULT_PARAMS['force3_size'], 
                                      step=1.0, key='f3_size')

# 显示说明
st.sidebar.markdown("""
<small>
📌 <b>说明：</b><br>
• F3的x坐标将自动计算<br>
• 确保 ΣFx=0, ΣFy=0, ΣMz=0
</small>
""", unsafe_allow_html=True)

st.sidebar.markdown("---")

# 计算按钮
if st.sidebar.button("🔍 计算力3 (自动平衡)", type="primary", use_container_width=True):
    # 将输入转换为总力（N）用于平衡计算
    length_scale_m = pixel_size_um * 1e-6  # m/px

    if force_input_mode == "牵引应力 (Pa)":
        # 总力 = 牵引应力 * 作用面积
        area1_m2 = (force1_size * length_scale_m) ** 2
        area2_m2 = (force2_size * length_scale_m) ** 2
        force1_mag_N = float(force1_traction_pa) * area1_m2
        force2_mag_N = float(force2_traction_pa) * area2_m2
    else:
        # 转换μN → N
        force1_mag_N = float(force1_magnitude) * 1e-6
        force2_mag_N = float(force2_magnitude) * 1e-6
    
    # 构建力1和力2
    Fx1, Fy1 = calculate_force_components(force1_mag_N, force1_angle)
    force1 = {
        'magnitude': force1_mag_N,  # 内部使用N
        'magnitude_uN': float(force1_mag_N) * 1e6,  # 用于显示
        'traction_pa': float(force1_traction_pa) if force_input_mode == "牵引应力 (Pa)" else None,
        'angle_deg': force1_angle,
        'position': (force1_x, force1_y),
        'square_size': force1_size,
        'Fx': Fx1,
        'Fy': Fy1
    }
    
    Fx2, Fy2 = calculate_force_components(force2_mag_N, force2_angle)
    force2 = {
        'magnitude': force2_mag_N,  # 内部使用N
        'magnitude_uN': float(force2_mag_N) * 1e6,
        'traction_pa': float(force2_traction_pa) if force_input_mode == "牵引应力 (Pa)" else None,
        'angle_deg': force2_angle,
        'position': (force2_x, force2_y),
        'square_size': force2_size,
        'Fx': Fx2,
        'Fy': Fy2
    }
    
    # 自动计算满足力矩平衡的F3位置
    result = find_balanced_position_for_force3(force1, force2, force3_size, y3=force3_y)
    
    if result is None:
        st.sidebar.error("❌ 无法计算平衡位置，请检查输入参数")
    else:
        force3_x_calculated = result['position'][0]
        force3_y_calculated = result['position'][1]
        
        # 使用计算出的位置
        force3_pos = {
            'position': (force3_x_calculated, force3_y_calculated),
            'square_size': force3_size
        }
        
        # 计算力3的大小和方向
        force3 = calculate_third_force(force1, force2, force3_pos)

    # 牵引应力模式下，附加力3的等效牵引应力（Pa）字段
    if force_input_mode == "牵引应力 (Pa)":
        area3_m2 = (force3_size * length_scale_m) ** 2
        force3['traction_pa'] = float(force3['magnitude']) / area3_m2 if area3_m2 > 0 else None

    forces = [force1, force2, force3]
    equilibrium_result = verify_equilibrium(forces)

    params = {
        'E': E_kPa,
        'nu': nu,
        'pixel_size_um': pixel_size_um,
        'field_width': field_width,
        'field_height': field_height,
        'boundary': boundary,
        'sampling_interval': sampling_interval,
        'force_input_mode': 'traction_stress' if force_input_mode == "牵引应力 (Pa)" else 'concentrated_force',
        'force1_traction_pa': float(force1_traction_pa) if force_input_mode == "牵引应力 (Pa)" else None,
        'force1_magnitude': float(force1_mag_N) * 1e6,
        'force1_angle': force1_angle,
        'force1_x': force1_x,
        'force1_y': force1_y,
        'force1_size': force1_size,
        'force2_traction_pa': float(force2_traction_pa) if force_input_mode == "牵引应力 (Pa)" else None,
        'force2_magnitude': float(force2_mag_N) * 1e6,
        'force2_angle': force2_angle,
        'force2_x': force2_x,
        'force2_y': force2_y,
        'force2_size': force2_size,
        'force3_x': force3_x_calculated,
        'force3_y': force3_y_calculated,
        'force3_size': force3_size,
    }

    st.session_state.force1 = force1
    st.session_state.force2 = force2
    st.session_state.force3 = force3
    st.session_state.forces = forces
    st.session_state.equilibrium_result = equilibrium_result
    st.session_state.params = params
    st.session_state.calculated = True
    st.session_state.displacement_computed = False
    st.session_state.calculation_explanation = result['explanation']

    st.sidebar.success("✅ 力3计算完成!")
    st.sidebar.info(f"📍 自动计算的x坐标: {force3_x_calculated:.2f} pixel")

# ========== 主区域 ==========

if st.session_state.calculated:
    # 创建标签页
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 结果概览", 
        "🎨 牵引力场可视化", 
        "📈 位移场可视化", 
        "💾 数据导出"
    ])
    
    # 标签页1: 结果概览
    with tab1:
        st.header("力3计算结果 (自动平衡)")
        
        # 显示计算说明
        if 'calculation_explanation' in st.session_state:
            st.info(f"🎯 {st.session_state.calculation_explanation}")
        
        force3 = st.session_state.force3
        
        # 使用更醒目的方式显示结果
        st.subheader("📊 力3参数")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("位置 X", f"{force3['position'][0]:.2f} px", 
                     delta="自动计算", delta_color="normal")
        with col2:
            st.metric("位置 Y", f"{force3['position'][1]:.2f} px",
                     delta="用户指定", delta_color="off")
        with col3:
            # 转换回μN显示
            force3_uN = force3['magnitude'] * 1e6
            st.metric("力大小", f"{force3_uN:.4f} μN")
        with col4:
            st.metric("力方向", f"{force3['angle_deg']:.2f}°")

        # 如果当前使用牵引应力模式，额外显示力3的等效牵引应力（Pa），以贴近论文表述
        if force3.get("traction_pa") is not None:
            st.caption(f"等效牵引应力（力3，均布在 {st.session_state.params.get('force3_size', 0):.0f}×{st.session_state.params.get('force3_size', 0):.0f} px²）："
                       f" **{force3['traction_pa']:.2f} Pa**")
        
        st.subheader("📐 力3分量")
        col1, col2 = st.columns(2)
        with col1:
            fx_uN = force3['Fx'] * 1e6
            st.metric("Fx (水平分量)", f"{fx_uN:.4f} μN")
        with col2:
            fy_uN = force3['Fy'] * 1e6
            st.metric("Fy (垂直分量)", f"{fy_uN:.4f} μN")
        
        st.markdown("---")
        
        st.subheader("✅ 平衡验证")
        eq_result = st.session_state.equilibrium_result
        
        result_text = format_equilibrium_result(eq_result)
        st.text(result_text)
        
        # 高亮显示平衡状态
        if eq_result['is_balanced']:
            st.success("🎉 系统完美平衡！所有平衡条件均满足 (ΣFx=0, ΣFy=0, ΣMz=0)")
        else:
            # 理论上不应该出现，但保留以防万一
            st.warning("⚠️ 注意：力矩平衡精度未达到默认阈值")
            st.info(f"力矩值: {eq_result['sum_Mz']:.6e} Pa·pixel (数值误差)")
        
        # 显示三力平衡的物理意义
        with st.expander("📖 三力平衡的物理意义"):
            # 从session_state获取所有力的信息
            force1 = st.session_state.force1
            force2 = st.session_state.force2
            
            st.markdown(f"""
            ### 🔬 物理原理
            
            **三力平衡的充要条件**：
            1. ✅ 合力为零：ΣF = 0
            2. ✅ 合力矩为零：ΣM = 0
            
            **本系统的计算策略**：
            - **输入**：F₁（完全确定）、F₂（完全确定）、F₃的y坐标
            - **计算**：F₃的x坐标、大小、方向
            - **保证**：严格满足所有平衡条件
            
            **当前配置**：
            - F₁ = {force1['magnitude']*1e6:.2f} μN @ {force1['angle_deg']:.1f}°, 位置({force1['position'][0]:.1f}, {force1['position'][1]:.1f})
            - F₂ = {force2['magnitude']*1e6:.2f} μN @ {force2['angle_deg']:.1f}°, 位置({force2['position'][0]:.1f}, {force2['position'][1]:.1f})
            - F₃ = {force3['magnitude']*1e6:.2f} μN @ {force3['angle_deg']:.1f}°, 位置({force3['position'][0]:.1f}, {force3['position'][1]:.1f})
            
            **几何意义**：
            三个力的作用线共点（或平行），形成一个稳定的平衡系统。
            """)
        
        # 检查是否存在重叠
        if check_squares_overlap(st.session_state.forces):
            st.warning("⚠️ 警告: 力作用区域存在重叠")
        
        # 求解位移按钮
        st.markdown("---")
        if st.button("🚀 求解位移场", type="primary", use_container_width=True):
            with st.spinner("正在计算位移场..."):
                # 创建进度条
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # 转换材料参数单位
                E_Pa = st.session_state.params['E'] * 1000  # kPa -> Pa
                nu_val = st.session_state.params['nu']
                
                # 创建网格
                status_text.text("正在构建计算网格...")
                progress_bar.progress(20)
                X, Y, x_vec, y_vec = create_displacement_grid(
                    field_width, field_height, boundary, sampling_interval
                )
                
                # 计算位移场
                status_text.text("正在计算位移场 (这可能需要一些时间)...")
                progress_bar.progress(40)
                
                # 推荐：SI单位自洽求解（贴近论文实现）
                # - forces 内部是总力(N) + 区域尺寸(pixel)
                # - 用 pixel_size_um 把区域面积换算为 m^2，得到牵引应力(Pa)
                u_x, u_y = compute_displacement_field_si(
                    X,
                    Y,
                    st.session_state.forces,
                    E_Pa,
                    nu_val,
                    pixel_size_um=st.session_state.params.get("pixel_size_um", 1.0),
                )
                
                # 计算位移幅值
                status_text.text("正在计算位移幅值...")
                progress_bar.progress(80)
                u_mag = compute_displacement_magnitude(u_x, u_y)
                
                # 检查位移量级
                max_displacement = np.max(u_mag)
                mean_displacement = np.mean(u_mag)
                
                # 保存结果
                st.session_state.X = X
                st.session_state.Y = Y
                st.session_state.x_vec = x_vec
                st.session_state.y_vec = y_vec
                st.session_state.u_x = u_x
                st.session_state.u_y = u_y
                st.session_state.u_mag = u_mag
                st.session_state.displacement_computed = True
                
                progress_bar.progress(100)
                status_text.text("✓ 计算完成!")
                time.sleep(0.5)
                status_text.empty()
                progress_bar.empty()
                
            st.success("✅ 位移场计算完成!")
            
            # 位移量级警告
            if max_displacement < 0.01:
                st.warning(f"⚠️ 位移很小（最大{max_displacement:.6f} pixel），PIV算法可能难以追踪")
                st.info("💡 建议：增大力（如2000-5000 μN）或减小杨氏模量（如0.5-2 kPa）")
            elif max_displacement < 0.1:
                st.info(f"ℹ️ 位移偏小（最大{max_displacement:.6f} pixel），需要高精度PIV算法")
            elif max_displacement > 10:
                st.warning(f"⚠️ 位移很大（最大{max_displacement:.2f} pixel），可能超出线性假设范围")
            else:
                st.success(f"✅ 位移量级适中（最大{max_displacement:.4f} pixel），适合PIV追踪")
            
            st.rerun()
    
    # 标签页2: 牵引力场可视化
    with tab2:
        st.header("牵引力场分布")
        
        # 添加显示选项
        col1, col2 = st.columns([3, 1])
        with col1:
            st.subheader("可视化选项")
            traction_style_label = st.radio(
                "配色风格",
                options=[
                    "经典（黑底绿箭头 + Jet红蓝热图）",
                    "科学（v1.3 顶刊柔和配色）",
                ],
                index=0,
                horizontal=True,
                help="用于对比/复现TFM常见图形时选“经典”；用于论文投稿更柔和耐看时选“科学”。",
            )
            traction_style = "classic" if traction_style_label.startswith("经典") else "scientific"
        with col2:
            arrow_density = st.slider("箭头密度", min_value=3, max_value=10, value=5, 
                                     help="调整每个力区域内箭头的数量")
        
        # 创建子标签
        sub_tab1, sub_tab2 = st.tabs(["热图+箭头", "仅箭头"])
        
        with sub_tab1:
            st.markdown("**牵引力场热图（带方向箭头）**")
            fig, ax = plt.subplots(figsize=FIGSIZE_SINGLE)
            plot_traction_field(
                st.session_state.forces, 
                (field_width, field_height), 
                ax=ax,
                show_arrows=True,
                arrow_density=arrow_density,
                style=traction_style,
                pixel_size_um=st.session_state.params.get("pixel_size_um", 1.0),
            )
            fig.tight_layout()
            show_fig_centered(fig, center_ratio=3)
            plt.close(fig)
            
            if traction_style == "classic":
                st.info("💡 经典风格：绿色箭头表示力的方向；热图使用Jet（蓝→红）显示牵引力大小。")
            else:
                st.info("💡 科学风格：箭头/热图使用柔和的顶刊配色，适合论文和长时间观察。")
        
        with sub_tab2:
            st.markdown("**仅显示力的方向箭头**")
            fig, ax = plt.subplots(figsize=FIGSIZE_SINGLE)
            plot_traction_field_arrows_only(
                st.session_state.forces, 
                (field_width, field_height), 
                ax=ax,
                arrow_density=arrow_density,
                style=traction_style,
            )
            fig.tight_layout()
            show_fig_centered(fig, center_ratio=3)
            plt.close(fig)
            
            if traction_style == "classic":
                st.info("💡 经典风格：黑底 + 绿色箭头（更接近很多TFM软件/论文的示意图风格）。")
            else:
                st.info("💡 科学风格：不同颜色的箭头代表不同的力（天蓝=力1，薄荷绿=力2，黄色=力3）。")
    
    # 标签页3: 位移场可视化
    with tab3:
        if st.session_state.displacement_computed:
            st.header("位移场分布")

            # 位移场配色风格（与牵引力场分开控制，方便你做对比图）
            displacement_style_label = st.radio(
                "位移场配色风格",
                options=[
                    "经典（红蓝Jet热图 / 黑底绿矢量示意）",
                    "科学（v1.3 顶刊柔和配色）",
                ],
                index=0,
                horizontal=True,
                help="想复现常见TFM对比图请选择“经典”；做论文图表且希望更柔和耐看请选择“科学”。",
            )
            displacement_style = "classic" if displacement_style_label.startswith("经典") else "scientific"
            
            # 子标签页
            sub_tab1, sub_tab2, sub_tab3, sub_tab4, sub_tab5 = st.tabs([
                "位移幅值", "x方向位移", "y方向位移", "并排对比", "位移矢量(示意)"
            ])
            
            with sub_tab1:
                fig, ax = plt.subplots(figsize=FIGSIZE_SINGLE)
                plot_displacement_field(
                    st.session_state.u_x, st.session_state.u_y,
                    st.session_state.X, st.session_state.Y,
                    st.session_state.forces, (field_width, field_height),
                    plot_type='magnitude', ax=ax, style=displacement_style
                )
                fig.tight_layout()
                show_fig_centered(fig, center_ratio=3)
                plt.close(fig)
                
                # 统计信息
                st.subheader("📊 统计信息")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("最大位移", f"{np.max(st.session_state.u_mag):.6e} pixel")
                with col2:
                    st.metric("最小位移", f"{np.min(st.session_state.u_mag):.6e} pixel")
                with col3:
                    st.metric("平均位移", f"{np.mean(st.session_state.u_mag):.6e} pixel")
                
                # 诊断信息
                st.subheader("🔍 诊断信息")
                col1, col2, col3, col4 = st.columns(4)
                
                nan_count = np.sum(np.isnan(st.session_state.u_mag))
                inf_count = np.sum(np.isinf(st.session_state.u_mag))
                max_ux = np.max(np.abs(st.session_state.u_x))
                max_uy = np.max(np.abs(st.session_state.u_y))
                
                with col1:
                    st.metric("NaN数量", nan_count, 
                             delta="正常" if nan_count == 0 else "异常",
                             delta_color="off" if nan_count == 0 else "inverse")
                with col2:
                    st.metric("Inf数量", inf_count,
                             delta="正常" if inf_count == 0 else "异常",
                             delta_color="off" if inf_count == 0 else "inverse")
                with col3:
                    st.metric("最大u_x", f"{max_ux:.6e} px")
                with col4:
                    st.metric("最大u_y", f"{max_uy:.6e} px")
                
                # 物理合理性说明
                with st.expander("💡 关于位移场的【不均匀】分布"):
                    st.markdown("""
                    ### ⚠️ 重要理解
                    
                    **均匀分布的力 ≠ 均匀的位移场**
                    
                    #### 为什么位移场不均匀？
                    
                    1. **力的分布**：
                       - ✅ 在每个正方形区域内，牵引力密度是**均匀的**
                       - ✅ 这意味着 p = F/A = 常数（在力作用区域内）
                    
                    2. **位移的物理特性**：
                       - ❌ 位移场**不应该**是均匀的
                       - ✅ 位移是**积分效应**，会随距离变化
                       - ✅ 位移随着离力源的距离增加而**衰减**
                    
                    #### 正确的位移场特征
                    
                    - **靠近力源**：位移较大
                    - **远离力源**：位移逐渐减小
                    - **无穷远处**：位移趋近于零
                    - **多力叠加**：产生复杂的波纹状图案
                    
                    #### 如何判断计算正确？
                    
                    检查以下指标：
                    1. ✅ NaN数量 = 0（无奇异值）
                    2. ✅ Inf数量 = 0（无无穷大）
                    3. ✅ 位移量级：$10^{{-6}}$ - $10^{{-3}}$ pixel（对于E=5kPa, F=18Pa）
                    4. ✅ 位移随距离衰减
                    
                    #### 物理类比
                    
                    想象在水面上按压一个正方形区域：
                    - 压力均匀分布
                    - 但水面变形**不均匀**
                    - 中心下陷，边缘影响减小
                    
                    **这是弹性力学的基本特性，不是计算错误！**
                    
                    详见：📄 `位移场计算说明.md`
                    """)
            
            with sub_tab2:
                fig, ax = plt.subplots(figsize=FIGSIZE_SINGLE)
                plot_displacement_field(
                    st.session_state.u_x, st.session_state.u_y,
                    st.session_state.X, st.session_state.Y,
                    st.session_state.forces, (field_width, field_height),
                    plot_type='x', ax=ax, style=displacement_style
                )
                fig.tight_layout()
                show_fig_centered(fig, center_ratio=3)
                plt.close(fig)
            
            with sub_tab3:
                fig, ax = plt.subplots(figsize=FIGSIZE_SINGLE)
                plot_displacement_field(
                    st.session_state.u_x, st.session_state.u_y,
                    st.session_state.X, st.session_state.Y,
                    st.session_state.forces, (field_width, field_height),
                    plot_type='y', ax=ax, style=displacement_style
                )
                fig.tight_layout()
                show_fig_centered(fig, center_ratio=3)
                plt.close(fig)
            
            with sub_tab4:
                fig = plot_comparison(
                    st.session_state.forces,
                    st.session_state.u_x, st.session_state.u_y,
                    st.session_state.X, st.session_state.Y,
                    (field_width, field_height),
                    traction_style=traction_style,
                    displacement_style=displacement_style,
                )
                fig.set_size_inches(*FIGSIZE_COMPARE, forward=True)
                fig.tight_layout()
                show_fig_centered(fig, center_ratio=5)
                plt.close(fig)

            with sub_tab5:
                st.markdown("**位移矢量示意图（黑底 + 绿色箭头 + 白色方框）**")
                col_a, col_b = st.columns([2, 1])
                with col_b:
                    skip = st.slider("矢量稀疏程度(跳点)", min_value=2, max_value=15, value=6, step=1,
                                     help="数值越大，箭头越稀疏（更清爽）。")
                    scale = st.slider("矢量缩放(越大越短)", min_value=0.1, max_value=5.0, value=1.0, step=0.1,
                                      help="用于让箭头长度更合适；一般默认即可。")

                with col_a:
                    fig, ax = plt.subplots(figsize=FIGSIZE_SINGLE)
                    plot_displacement_vectors_only(
                        st.session_state.u_x,
                        st.session_state.u_y,
                        st.session_state.X,
                        st.session_state.Y,
                        st.session_state.forces,
                        (field_width, field_height),
                        skip=skip,
                        scale=scale,
                        ax=ax,
                        style=displacement_style,
                    )
                    fig.tight_layout()
                    show_fig_centered(fig, center_ratio=3)
                    plt.close(fig)

                if displacement_style == "classic":
                    st.info("💡 经典示意：黑底 + 绿色位移矢量，更接近常见TFM示意图风格。")
                else:
                    st.info("💡 科学示意：深蓝黑底 + 白色位移矢量，整体更柔和。")
        else:
            st.info("ℹ️ 请先在【结果概览】标签页中点击【求解位移场】按钮")
    
    # 标签页4: 数据导出
    with tab4:
        st.header("数据导出")
        
        st.subheader("1. 导出力数据")
        st.write("导出包含所有力的位置、大小、方向和平衡验证结果的MAT文件")
        
        if st.button("📥 下载力数据 (MAT)", use_container_width=True):
            params = st.session_state.params.copy()
            params['equilibrium_result'] = st.session_state.equilibrium_result
            
            filename = export_forces_to_mat(
                st.session_state.forces, 
                params, 
                'forces_data.mat'
            )
            st.success(f"✅ 已导出到: {filename}")
            
            # 提供下载
            with open(filename, 'rb') as f:
                st.download_button(
                    label="💾 下载文件",
                    data=f,
                    file_name=filename,
                    mime="application/octet-stream"
                )
        
        st.markdown("---")
        
        st.subheader("2. 导出位移场数据")
        
        if st.session_state.displacement_computed:
            st.write("导出包含位移场的MAT文件(简化格式: pos和vec)")
            
            if st.button("📥 下载位移数据 (MAT简化版)", use_container_width=True):
                pos, vec = prepare_displacement_export(
                    st.session_state.X, 
                    st.session_state.Y,
                    st.session_state.u_x, 
                    st.session_state.u_y
                )
                
                filename = export_displacement_to_mat(pos, vec, 'displacement_field.mat')
                st.success(f"✅ 已导出到: {filename}")
                
                # 提供下载
                with open(filename, 'rb') as f:
                    st.download_button(
                        label="💾 下载文件",
                        data=f,
                        file_name=filename,
                        mime="application/octet-stream"
                    )
            
            st.write("导出完整位移场数据(包含网格和元数据)")
            
            if st.button("📥 下载位移数据 (MAT完整版)", use_container_width=True):
                params = st.session_state.params
                
                filename = export_displacement_full(
                    st.session_state.X, st.session_state.Y,
                    st.session_state.u_x, st.session_state.u_y,
                    st.session_state.forces,
                    params,
                    'displacement_full.mat'
                )
                st.success(f"✅ 已导出到: {filename}")
                
                # 提供下载
                with open(filename, 'rb') as f:
                    st.download_button(
                        label="💾 下载文件",
                        data=f,
                        file_name=filename,
                        mime="application/octet-stream"
                    )
        else:
            st.info("ℹ️ 请先计算位移场")
        
        st.markdown("---")
        
        st.subheader("3. 生成合成荧光图像")
        st.write("基于位移场数据生成TIF格式的参考图像和变形图像（用于TFM算法测试）")
        
        if st.session_state.displacement_computed:
            with st.form("image_generation_form"):
                st.markdown("#### 📸 图像生成参数")
                
                # 创建标签页
                tab1, tab2 = st.tabs(["🔬 显微镜参数", "🎨 图像参数"])
                
                with tab1:
                    st.markdown("##### 光学系统参数")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # 荧光基团选择
                        fluorophore_options = {
                            "FITC": {"ex": 495, "em": 519},
                            "GFP": {"ex": 488, "em": 507},
                            "Texas Red": {"ex": 595, "em": 615},
                            "Cy3": {"ex": 550, "em": 570},
                            "Cy5": {"ex": 650, "em": 670},
                            "mCherry": {"ex": 587, "em": 610},
                            "DAPI": {"ex": 358, "em": 461},
                            "Custom": {"ex": 530, "em": 560}
                        }
                        
                        fluorophore = st.selectbox(
                            "荧光基团",
                            options=list(fluorophore_options.keys()),
                            index=1,  # 默认GFP
                            help="选择荧光珠使用的荧光基团"
                        )
                        
                        excitation_wavelength = st.number_input(
                            "激发光波长 (nm)",
                            min_value=300, max_value=800,
                            value=fluorophore_options[fluorophore]["ex"],
                            step=1,
                            help="激发光的中心波长"
                        )
                        
                        emission_wavelength = st.number_input(
                            "发射光波长 (nm)",
                            min_value=350, max_value=900,
                            value=fluorophore_options[fluorophore]["em"],
                            step=1,
                            help="发射光的中心波长"
                        )
                        
                        numerical_aperture = st.number_input(
                            "数值孔径 (NA)",
                            min_value=0.1, max_value=1.7,
                            value=1.4, step=0.05,
                            help="物镜的数值孔径，影响分辨率"
                        )
                    
                    with col2:
                        pixel_size = st.number_input(
                            "像素大小 (μm/pixel)",
                            min_value=0.01, max_value=1.0,
                            value=0.108, step=0.001,
                            format="%.3f",
                            help="相机像素对应的物理尺寸"
                        )
                        
                        exposure_time = st.number_input(
                            "曝光时间 (ms)",
                            min_value=1.0, max_value=1000.0,
                            value=50.0, step=1.0,
                            help="相机曝光时间"
                        )
                        
                        time_interval = st.number_input(
                            "时间间隔 (s)",
                            min_value=0.1, max_value=600.0,
                            value=1.0, step=0.1,
                            help="参考图像和变形图像之间的时间间隔"
                        )
                        
                        bit_depth = st.selectbox(
                            "相机位深度",
                            options=[8, 12, 14, 16],
                            index=3,  # 默认16-bit
                            help="相机的位深度"
                        )
                        
                        sampling_mode = st.selectbox(
                            "采样模式",
                            options=["Widefield", "Confocal", "TIRF", "Spinning Disk"],
                            index=0,
                            help="显微镜采样模式"
                        )
                
                with tab2:
                    st.markdown("##### 荧光珠和图像参数")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        num_beads = st.number_input("荧光珠数量", 
                                                   min_value=50, max_value=5000, 
                                                   value=500, step=50,
                                                   help="场内随机分布的荧光珠数量")
                        
                        use_psf = st.checkbox(
                            "使用物理PSF模型",
                            value=True,
                            help="根据光学参数自动计算点扩散函数(PSF)"
                        )
                        
                        if not use_psf:
                            bead_sigma = st.number_input("光斑标准差 (pixel)", 
                                                        min_value=0.5, max_value=5.0, 
                                                        value=2.0, step=0.1,
                                                        help="手动设置高斯光斑的标准差")
                        
                        bead_intensity = st.number_input("荧光珠亮度", 
                                                        min_value=100.0, max_value=10000.0, 
                                                        value=2000.0, step=100.0,
                                                        help="荧光珠的峰值强度")
                    
                    with col2:
                        noise_level = st.number_input("噪声水平", 
                                                     min_value=0.0, max_value=200.0, 
                                                     value=50.0, step=10.0,
                                                     help="高斯噪声的标准差")
                        
                        background = st.number_input("背景亮度", 
                                                    min_value=0.0, max_value=500.0, 
                                                    value=100.0, step=10.0,
                                                    help="图像背景的基础亮度")
                        
                        random_seed = st.number_input("随机种子", 
                                                     min_value=0, max_value=99999, 
                                                     value=42, step=1,
                                                     help="设置随机种子以获得可重复的结果")
                        
                        apply_shot_noise = st.checkbox(
                            "添加散粒噪声",
                            value=False,
                            help="模拟真实的Poisson噪声"
                        )

                        st.markdown("##### 🧪 PIV/TFM自检（非常关键）")
                        # 传统TFM的“牵引力像噪声”，几乎总是因为这里的位移量级太小导致PIV追踪失败
                        if "u_mag" in st.session_state:
                            u_mag_now = st.session_state.u_mag
                            u_max = float(np.nanmax(u_mag_now))
                            u_mean = float(np.nanmean(u_mag_now))
                        else:
                            u_max = 0.0
                            u_mean = 0.0

                        st.caption(f"当前位移场：max={u_max:.6f} px, mean={u_mean:.6f} px")
                        if u_max < 0.05:
                            st.error("⚠️ 位移太小：传统PIV/TFM大概率只会输出噪声（牵引力图就像噪音）。")
                            st.caption("优先建议：增大力(μN) 或减小E(kPa)，让 max 位移进入 0.1-2 px。")
                        elif u_max < 0.1:
                            st.warning("ℹ️ 位移偏小：部分PIV设置下可能不稳定。建议让 max 位移 ≥ 0.1 px。")
                        else:
                            st.success("✅ 位移量级对PIV比较友好。")

                        target_max_px = 0.5  # 经验目标：0.3-0.8 px 最容易追踪
                        suggested_scale = float(np.clip(target_max_px / u_max, 1.0, 50.0)) if u_max > 0 else 1.0
                        displacement_scale = st.slider(
                            "生成图像用位移放大倍数（仅影响合成图像）",
                            min_value=1.0,
                            max_value=50.0,
                            value=suggested_scale,
                            step=0.5,
                            help="当你必须用某组物理参数但位移过小、导致传统TFM输出噪声时，用这个把位移放大到可追踪范围。",
                        )

                        tif_compat_mode = st.checkbox(
                            "TIFF兼容模式（无压缩 + 不写ImageJ元数据，最兼容传统软件）",
                            value=True,
                            help="部分老TFM/MATLAB流程对压缩/带ImageJ元数据的TIFF支持不好，会读出异常。",
                        )
                
                # 提交按钮
                generate_images = st.form_submit_button("🎨 生成完整TFM图像", 
                                                       use_container_width=True,
                                                       type="primary")
            
            if generate_images:
                with st.spinner("正在生成合成荧光图像..."):
                    try:
                        # 创建进度指示
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        # 计算PSF sigma
                        if use_psf:
                            bead_sigma = calculate_psf_sigma(
                                emission_wavelength, 
                                numerical_aperture, 
                                pixel_size
                            )
                            st.info(f"✓ 根据光学参数计算PSF: σ = {bead_sigma:.3f} pixel")
                        
                        # 步骤1: 生成荧光珠位置
                        status_text.text("步骤 1/5: 生成荧光珠位置...")
                        progress_bar.progress(20)
                        
                        beads = generate_bead_positions(
                            field_width, field_height, 
                            num_beads=num_beads,
                            boundary=boundary,
                            min_distance=bead_sigma * 3,  # 最小距离为3倍sigma
                            seed=random_seed
                        )
                        
                        # 步骤2: 生成参考图像
                        status_text.text("步骤 2/5: 生成参考图像...")
                        progress_bar.progress(40)
                        
                        ref_image = generate_reference_image(
                            beads, field_width, field_height,
                            sigma=bead_sigma,
                            intensity=bead_intensity,
                            noise_level=noise_level,
                            background=background,
                            noise_mode="independent_gaussian",
                            random_seed=random_seed
                        )
                        
                        # 步骤3: 生成变形图像
                        status_text.text("步骤 3/5: 生成变形图像...")
                        progress_bar.progress(60)
                        
                        def_image, displaced_beads = generate_deformed_image(
                            beads, 
                            st.session_state.X, st.session_state.Y,
                            st.session_state.u_x, st.session_state.u_y,
                            field_width, field_height,
                            sigma=bead_sigma,
                            intensity=bead_intensity,
                            noise_level=noise_level,
                            background=background,
                            displacement_scale=displacement_scale,
                            noise_mode="independent_gaussian",
                            random_seed=random_seed + 1
                        )

                        # 可选：添加散粒噪声（更贴近真实显微镜）
                        if apply_shot_noise:
                            ref_image = apply_shot_noise_fn(ref_image)
                            def_image = apply_shot_noise_fn(def_image)
                        
                        # 计算位移统计
                        displacement_mag = np.sqrt(
                            (displaced_beads[:, 0] - beads[:, 0])**2 +
                            (displaced_beads[:, 1] - beads[:, 1])**2
                        )
                        
                        # 步骤4: 准备元数据
                        status_text.text("步骤 4/5: 准备元数据...")
                        progress_bar.progress(80)
                        
                        metadata = {
                            'sampling_mode': sampling_mode,
                            'fluorophore': fluorophore,
                            'excitation_wavelength': excitation_wavelength,
                            'emission_wavelength': emission_wavelength,
                            'exposure_time': exposure_time,
                            'pixel_size': pixel_size,
                            'time_interval': time_interval,
                            'numerical_aperture': numerical_aperture,
                            'bit_depth': bit_depth,
                            'bead_count': len(beads),
                            'psf_sigma': bead_sigma,
                            'bead_intensity': bead_intensity,
                            'noise_level': noise_level,
                            'background': background,
                            'max_displacement': np.max(displacement_mag),
                            'mean_displacement': np.mean(displacement_mag),
                            'displacement_scale': displacement_scale,
                            'random_seed': random_seed
                        }
                        
                        # 步骤5: 保存图像
                        status_text.text("步骤 5/5: 保存带元数据的TIF文件...")
                        progress_bar.progress(90)
                        
                        ref_filename, def_filename = save_image_pair_with_metadata(
                            ref_image, def_image,
                            metadata,
                            ref_filename='reference.tif',
                            def_filename='deformed.tif',
                            compression=None if tif_compat_mode else "deflate",
                            imagej=(not tif_compat_mode)
                        )
                        
                        # 保存到session state
                        st.session_state.ref_image = ref_image
                        st.session_state.def_image = def_image
                        st.session_state.bead_positions = beads
                        st.session_state.displaced_beads = displaced_beads
                        st.session_state.image_metadata = metadata
                        st.session_state.images_generated = True
                        
                        progress_bar.progress(100)
                        status_text.text("✓ 完成!")
                        
                        st.success("✅ 带完整元数据的TFM图像生成成功!")
                        st.info(f"📐 PSF Sigma: {bead_sigma:.3f} pixel | "
                               f"📍 位移范围: {np.min(displacement_mag):.4f} - {np.max(displacement_mag):.4f} pixel")
                        
                    except Exception as e:
                        st.error(f"❌ 生成图像时出错: {str(e)}")
                        import traceback
                        st.code(traceback.format_exc())
            
            # 显示生成的图像
            if 'images_generated' in st.session_state and st.session_state.images_generated:
                st.markdown("---")
                st.subheader("📷 生成的图像预览")
                
                # 将16-bit图像转换为8-bit用于显示
                def normalize_for_display(img_16bit):
                    """将16-bit图像归一化到[0, 255]用于显示"""
                    img_min = img_16bit.min()
                    img_max = img_16bit.max()
                    if img_max > img_min:
                        img_normalized = ((img_16bit - img_min) / (img_max - img_min) * 255).astype(np.uint8)
                    else:
                        img_normalized = np.zeros_like(img_16bit, dtype=np.uint8)
                    return img_normalized
                
                ref_display = normalize_for_display(st.session_state.ref_image)
                def_display = normalize_for_display(st.session_state.def_image)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**参考图像 (Reference)**")
                    st.image(ref_display, 
                            caption=f"参考图像 - {len(st.session_state.bead_positions)} 个荧光珠",
                            use_container_width=True)
                    
                    # 下载按钮
                    with open('reference.tif', 'rb') as f:
                        st.download_button(
                            label="📥 下载参考图像 (16-bit TIF)",
                            data=f,
                            file_name="reference.tif",
                            mime="image/tiff",
                            use_container_width=True
                        )
                
                with col2:
                    st.markdown("**变形图像 (Deformed)**")
                    st.image(def_display, 
                            caption=f"变形图像 - 应用位移场后",
                            use_container_width=True)
                    
                    # 下载按钮
                    with open('deformed.tif', 'rb') as f:
                        st.download_button(
                            label="📥 下载变形图像 (16-bit TIF)",
                            data=f,
                            file_name="deformed.tif",
                            mime="image/tiff",
                            use_container_width=True
                        )
                
                # 统计信息
                st.markdown("#### 📊 图像信息")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("图像尺寸", f"{field_width:.0f}×{field_height:.0f}")
                with col2:
                    st.metric("荧光珠数量", len(st.session_state.bead_positions))
                with col3:
                    displacement_mag = np.sqrt(
                        (st.session_state.displaced_beads[:, 0] - st.session_state.bead_positions[:, 0])**2 +
                        (st.session_state.displaced_beads[:, 1] - st.session_state.bead_positions[:, 1])**2
                    )
                    st.metric("平均位移", f"{np.mean(displacement_mag):.6f} px")
                with col4:
                    st.metric("最大位移", f"{np.max(displacement_mag):.6f} px")
                
                # 显示完整元数据
                if 'image_metadata' in st.session_state:
                    with st.expander("🔬 查看完整元数据（已保存到TIF文件）"):
                        metadata = st.session_state.image_metadata
                        
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.markdown("**显微镜参数**")
                            st.text(f"采样模式: {metadata.get('sampling_mode', 'N/A')}")
                            st.text(f"荧光基团: {metadata.get('fluorophore', 'N/A')}")
                            st.text(f"激发光: {metadata.get('excitation_wavelength', 'N/A')} nm")
                            st.text(f"发射光: {metadata.get('emission_wavelength', 'N/A')} nm")
                        
                        with col2:
                            st.markdown("**相机参数**")
                            st.text(f"像素大小: {metadata.get('pixel_size', 'N/A')} μm")
                            st.text(f"曝光时间: {metadata.get('exposure_time', 'N/A')} ms")
                            st.text(f"位深度: {metadata.get('bit_depth', 'N/A')} bit")
                            st.text(f"时间间隔: {metadata.get('time_interval', 'N/A')} s")
                        
                        with col3:
                            st.markdown("**光学参数**")
                            st.text(f"数值孔径: {metadata.get('numerical_aperture', 'N/A')}")
                            st.text(f"PSF Sigma: {metadata.get('psf_sigma', 'N/A'):.3f} px")
                            st.text(f"荧光珠亮度: {metadata.get('bead_intensity', 'N/A')}")
                            st.text(f"噪声水平: {metadata.get('noise_level', 'N/A')}")
                        
                        st.markdown("---")
                        st.markdown("**位移场信息**")
                        st.text(f"最大位移: {metadata.get('max_displacement', 'N/A'):.6f} pixel")
                        st.text(f"平均位移: {metadata.get('mean_displacement', 'N/A'):.6f} pixel")
                        st.text(f"随机种子: {metadata.get('random_seed', 'N/A')}")
                
                # 使用说明
                with st.expander("📖 如何使用生成的图像"):
                    st.markdown("""
                    ### 图像说明
                    
                    **参考图像 (reference.tif)**:
                    - 荧光珠在未受力时的初始位置
                    - 用作TFM算法的参考图像
                    
                    **变形图像 (deformed.tif)**:
                    - 荧光珠在受力变形后的位置
                    - 基于计算的位移场移动荧光珠
                    
                    ### 用途
                    
                    1. **TFM算法测试**: 使用这对图像测试PIV或其他位移追踪算法
                    2. **算法验证**: 已知真实位移场，可以验证算法精度
                    3. **参数优化**: 测试不同参数对算法性能的影响
                    
                    ### 工作流程
                    
                    ```
                    1. 生成图像对 (本程序)
                    2. 使用PIV/DIC算法追踪位移
                    3. 对比真实位移场与计算位移场
                    4. 评估算法精度
                    ```
                    
                    ### 图像格式
                    
                    - 格式: 16-bit TIFF
                    - 灰度值范围: 0-65535
                    - 兼容ImageJ、MATLAB、Python等
                    """)
        else:
            st.info("ℹ️ 请先计算位移场后才能生成合成图像")

        st.markdown("---")
        st.subheader("4. 生成算法输入数据包（zip）")
        st.write("按 `ALGORITHMS_AND_DATASETS_INPUTS.md` 的约定，生成各算法可直接读取的输入文件（图像/清单/位移.mat）。")

        images_ready = bool(getattr(st.session_state, "images_generated", False))
        if not images_ready:
            st.info("ℹ️ u-inferforce/pyTFM 需要 before/after 图像。请先在上方生成合成荧光图像；否则只能导出 Easy-to-use 的位移输入。")

        col_a, col_b, col_c = st.columns([2, 2, 2])
        with col_a:
            include_uinferforce = st.checkbox(
                "u-inferforce（manifest + Ref/Targ 图像）",
                value=images_ready,
                disabled=not images_ready,
            )
            include_pytfm = st.checkbox(
                "pyTFM（before/after 图像 + out.txt）",
                value=images_ready,
                disabled=not images_ready,
            )
            include_easy = st.checkbox(
                "Easy-to-use（input_data.mat：位移 pos/vec）",
                value=True,
            )

        with col_b:
            case_id = st.text_input(
                "case_id（zip 根目录名）",
                value=datetime.now().strftime("case_%Y%m%d_%H%M%S"),
                help="用于区分不同力场/参数的导出包。",
            )
            pytfm_frame_id = st.text_input(
                "pyTFM frame id（文件前缀）",
                value="01",
                help="将生成 `<frame>before.tif` 与 `<frame>after.tif`，例如 01before.tif。",
            )

        with col_c:
            pixelsize_um_for_algos = st.number_input(
                "pixelsize (μm/px)（写入pyTFM参数）",
                min_value=0.001,
                max_value=10.0,
                value=float(st.session_state.params.get("pixel_size_um", 1.0)),
                step=0.001,
                format="%.3f",
            )
            window_size_px = st.number_input(
                "pyTFM window_size (px)",
                min_value=8,
                max_value=256,
                value=64,
                step=4,
            )
            overlap_px = st.number_input(
                "pyTFM overlap (px)",
                min_value=0,
                max_value=255,
                value=32,
                step=4,
            )

        if st.button("📦 生成并下载算法输入数据包 (ZIP)", use_container_width=True):
            try:
                pos, vec = prepare_displacement_export(
                    st.session_state.X,
                    st.session_state.Y,
                    st.session_state.u_x,
                    st.session_state.u_y,
                )

                zip_bytes = build_algorithm_inputs_zip(
                    case_id=case_id,
                    ref_image=st.session_state.ref_image if images_ready else None,
                    def_image=st.session_state.def_image if images_ready else None,
                    pos=pos,
                    vec=vec,
                    forces=st.session_state.forces if "forces" in st.session_state else None,
                    metadata=st.session_state.image_metadata if "image_metadata" in st.session_state else None,
                    include_uinferforce=include_uinferforce,
                    include_pytfm=include_pytfm,
                    include_easy_to_use=include_easy,
                    pytfm_frame_id=pytfm_frame_id.strip() or "01",
                    pytfm_params=PyTFMParams(
                        pixelsize_um=float(pixelsize_um_for_algos),
                        window_size_px=int(window_size_px),
                        overlap_px=int(overlap_px),
                    ),
                    tiff_compat_mode=True,
                )

                st.download_button(
                    label="⬇️ 下载 ZIP",
                    data=zip_bytes,
                    file_name=f"{case_id}.zip",
                    mime="application/zip",
                    use_container_width=True,
                )
                st.success("✅ 已生成算法输入数据包，可直接用于各算法/对比脚本。")
            except Exception as e:
                st.error(f"❌ 生成ZIP失败: {e}")

else:
    # 未计算时的提示
    st.info("👈 请在左侧设置参数,然后点击【计算力3】按钮开始")
    
    # 显示说明
    st.markdown("""
    ## 📖 使用说明
    
    ### 1. 输入材料参数
    - **杨氏模量 E**: 材料的弹性模量，单位 kPa
    - **泊松比 ν**: 材料的横向应变与纵向应变之比，通常在 -1 到 0.5 之间
    
    ### 2. 设置计算场
    - **场宽度/高度**: 计算区域的尺寸，单位 pixel
    - **边界**: 场边缘不计算的区域宽度
    - **采样间距**: 位移场计算的网格间距
    
    ### 3. 输入已知力（力1和力2）
    - **大小**: 力的幅值，单位 Pa
    - **方向**: 力的方向角，单位度（0°为x正向，逆时针为正）
    - **位置**: 力的作用点坐标 (x, y)，单位 pixel
    - **正方形边长**: 力的作用区域大小，单位 pixel
    
    ### 4. 设置力3参数
    - **位置 y**: 指定力3的y坐标（可选，系统会选择合理默认值）
    - **正方形边长**: 力3的作用区域大小
    - 💡 **位置 x、大小、方向将自动计算**，以严格满足力和力矩平衡
    
    ### 5. 计算力3
    - 点击 **"🔍 计算力3 (自动平衡)"** 按钮
    - 系统自动计算力3的完整配置
    - ✅ 保证 ΣFx=0, ΣFy=0, ΣMz=0 严格满足
    
    ### 6. 求解位移场
    - 在"结果概览"页面，点击 **"🚀 求解位移场"**
    - 系统基于BIS方法计算基底的位移分布
    - 可在"位移场可视化"查看结果
    
    ### 7. 导出数据
    - 在"数据导出"页面下载 MAT 格式文件
    - 可导出力数据和位移场数据，便于 MATLAB 分析
    
    ---
    
    ### 💡 关键特性
    
    - **自动平衡**: 系统自动计算满足所有平衡条件的力3配置
    - **物理准确**: 严格遵循力学平衡方程
    - **简单易用**: 只需指定力1、力2和力3的y坐标即可
    """)
    
    # 添加物理背景说明
    with st.expander("🔬 物理背景 - 三力平衡系统"):
        st.markdown("""
        ### 三力平衡的数学约束
        
        对于三个力 F₁, F₂, F₃ 构成的平衡系统，必须满足：
        
        **力平衡方程（2个）：**
        ```
        ΣFx = F₁x + F₂x + F₃x = 0
        ΣFy = F₁y + F₂y + F₃y = 0
        ```
        
        **力矩平衡方程（1个）：**
        ```
        ΣMz = (x₁F₁y - y₁F₁x) + (x₂F₂y - y₂F₂x) + (x₃F₃y - y₃F₃x) = 0
        ```
        
        ### 本程序的求解策略
        
        **已知量（7个）：**
        - F₁: 大小、方向、位置(x₁, y₁) → 4个参数
        - F₂: 大小、方向、位置(x₂, y₂) → 4个参数
        - F₃: y₃坐标 → 1个参数
        
        **未知量（3个）：**
        - F₃: x₃坐标、大小、方向 → 3个参数
        
        **方程数：3个**（ΣFx=0, ΣFy=0, ΣMz=0）
        
        → **方程数 = 未知数个数**，系统有唯一解！
        
        ### 物理意义
        
        三力平衡的几何条件是：**三个力的作用线共点**（或平行）
        
        本程序通过数值计算自动找到满足此条件的力3配置。
        """)

# 页脚
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray;'>
    <p>BIS方法牵引力-位移场计算器 v1.0 | 基于Boussinesq解的积分形式</p>
</div>
""", unsafe_allow_html=True)

