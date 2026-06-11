# TFMLAB

用于 4D 牵引力显微镜（4D TFM）的 MATLAB 工具箱。

- **源代码库**：https://github.com/ElsevierSoftwareX/SOFTX-D-20-00104
- **版本**：1.0
- **许可证**：LGPL v3
- **作者**：MAtrix, KU Leuven & Universidad de Sevilla（jorge.barrasafano@kuleuven.be）

纳入本仓库用于算法基准对比，为了适应当前主流环境运行，部分代码做了修改。

---

## 环境要求

- MATLAB 2018a 及以上
- [DIPImage 3.x](http://www.diplib.org/download)（必须，图像处理核心库）
- [FreeFEM++ v4.7-1](https://github.com/FreeFem/FreeFem-sources/releases)（可选，非线性 FEM 求解）
- Abaqus（可选，商业 FEM 求解）
- [Paraview](https://www.paraview.org/download/)（可选，3D 可视化）

> DIPImage 和 Elastix 二进制文件体积较大，不随本仓库分发，需自行下载安装。

---

## 安装与运行

```matlab
% 检查依赖是否就绪
install_tfmlab

% 启动 GUI 工作流
main
```

详细操作步骤和参数说明见 `manual.pdf`。

---

## 目录结构

```
TFMLAB（SOFTX-D-20-00104-main）/
├── main.m                  # 主入口，启动 GUI 工作流
├── parameterFile.m         # 参数配置文件
├── install_tfmlab.m        # 依赖检查与安装向导
├── tfmlab_doctor.m         # 环境诊断工具 如果发现TFMLAB无法运行可以先运行该文件检查问题
├── manual.pdf              # 完整操作手册
│
├── cellMat/                # 图像处理流程
│   ├── imProcessing/       # 滤波、细胞分割、漂移校正
│   ├── dispCalc/           # 位移场计算（基于 Elastix FFD 配准）
│   └── im2mat/             # 图像文件加载
│
├── tractionRecovery/       # 牵引力场反演
│   ├── mechanics/          # 线性 / 非线性力学求解器
│   ├── solver/             # 正问题 / 逆问题求解
│   ├── tools_freefem/      # FreeFEM++ 接口
│   └── tools_abaqus/       # Abaqus 接口
│
├── results2Paraview/       # 结果导出（VTK 格式，供 Paraview/GID）
├── microscope2Tif/         # 显微镜格式（.lif）转 TIFF
├── guis/                   # MATLAB App Designer GUI 文件
├── bfmatlab/               # Bio-Formats MATLAB 接口
├── NIfTI_tools/            # NIfTI 格式读写工具
└── utilities/              # 公共辅助函数
```

---

## 引用

如使用 TFMLAB，请引用以下文献：

- Barrasa-Fano et al. (2020). TFMLAB: a MATLAB toolbox for 4D traction force microscopy. *bioRxiv*. doi:10.1101/2020.12.18.423056
- Sanz-Herrera et al. (2020). Inverse method based on 3D nonlinear physically constrained minimisation in TFM. *Soft Matter*.
- Barrasa-Fano et al. (2020). Advanced in silico validation framework for 3D TFM. *bioRxiv*. doi:10.1101/2020.12.08.411603
