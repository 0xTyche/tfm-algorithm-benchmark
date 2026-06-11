# tfm-ground-truth

基于 BIS（Boussinesq Integration Solution）方法的 TFM 模拟数据生成平台，用于构建可复现的"牵引应力场—位移场"ground truth，支持 Level A 和 Level B 两种算法评估场景。

- Level A：导出位移场（pos/vec）作为牵引反演算法的直接输入
- Level B：生成合成荧光微珠图像对（reference/deformed TIFF），用于端到端 PIV → 牵引反演流程测试

## 安装

```bash
pip install -r requirements.txt
```

## 运行

```bash
streamlit run app.py
```


## 目录结构

```
tfm-ground-truth/
├── app.py                                 # Streamlit 主入口
├── requirements.txt
├── modules/
│   ├── bis.py                             # BIS 位移场解析积分计算
│   ├── force_balance.py                   # 三力平衡求解
│   ├── displacement.py                    # 位移场工具函数
│   ├── visualization.py                   # 牵引力场与位移场可视化
│   ├── image_generator.py                 # 合成微珠图像生成（高斯 PSF）
│   ├── data_export.py                     # MAT 与 TIFF 导出
│   ├── algorithm_inputs.py                # 各算法输入格式打包
│   ├── fluorophore_database.py            # 11 种荧光团 PSF 预设参数
│   └── color_schemes.py
├── utils/
│   └── helpers.py
├── assets/                                # 项目示意图（PDF/PNG，供文章或文档使用）
├── render_project_schematic.py            # 生成流程示意图（输出到 assets/）
└── create_MovieData_from_u_inferforce.m   # 将导出位移转为 u-inferforce MovieData 格式
```

## 物理模型与单位

平台假设各向同性线弹性半空间（z = 0 表面），材料参数为杨氏模量 E（输入单位 kPa）和泊松比 ν。默认像素尺寸为 1 μm/pixel，即像素与 μm 数值等价。

牵引加载以"方形区域内均匀牵引应力"表示（单位 Pa）。对于边长为 s pixel 的区域，其合力为：

    F = t × (s × pixel_size_um × 1e-6)²  [N]

位移场通过 BIS 计算：对经典 Boussinesq 点力 Green 函数在各方形区域上解析积分，消除作用点奇异性，得到稳定闭式表达式。位移场空间分布随距离衰减，多个力叠加时会产生非均匀干涉形态，这是线弹性响应的正常结果。

## 三力平衡

平台接受两个用户定义的力（位置、方向、大小）加第三力的几何约束（位置和作用区域大小），自动求解第三力以满足：

    ΣFx = 0,  ΣFy = 0,  ΣMz = 0

三力平衡是 TFM 评测场景的必要条件（不平衡的牵引场会导致基底整体平移）。

## 参数选择与 PIV 位移范围

对于基于 PIV 的位移追踪，位移幅值建议在 0.1–2 pixel 范围内。低于 0.1 pixel 时热漂移和光学噪声占主导，高于 2 pixel 时相关追踪易失效。

默认参数（E = 1 kPa，F = 2000 μN，500×500 pixel 场，1 μm/pixel）下位移幅值约为 0.3–0.8 pixel，可被主流 PIV 软件稳定追踪。如果调整了材料参数或力大小，建议先在平台中确认位移范围后再生成图像对。

## 导出格式

数据导出页提供三类输出：

1. 力/牵引信息（MAT）：各力的几何参数、合力分量与平衡验证信息。

2. 位移场（MAT，Level A 输入）：
   - 简化格式：`pos`（N×2，采样点像素坐标）和 `vec`（N×2，像素位移），适配大多数 MATLAB/Python 后处理和牵引反演算法。
   - 完整格式：含网格、位移分量、幅值与统计量。

3. 合成微珠图像对（TIFF，Level B 输入）：16-bit 灰度图，reference 帧为随机微珠分布加高斯 PSF 与噪声，deformed 帧按位移场平移微珠位置后重建。平台内置位移量级自检，可选位移放大倍率以调整至 PIV 可追踪范围。

平台还可以将同一场景打包为各算法可直接读取的输入压缩包（zip），目前支持 u-inferforce、pyTFM 和 Easy-to-use TFM 的输入格式。
