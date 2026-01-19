# Easy-to-use_TFM_package

This Matlab package is a user-friendly tool for calculation of traction forces 
in traction force microscopy (TFM) experiments.  

After downloading, the program can be directly started from the Matlab command line
by entering "TF_reconstruction". The folder ''test_data'' contains an exemplary synthetic
data set that can be used for first tests.

The package contains two methods: 

1. Regularized Fourier Transform Traction Cytometry 

2. Bayesian Fourier Transform Traction Cytometry, which is an improved method for
automatic, robust traction calculation.

See the User Manual for details on program usage. 

---

## 中文：本项目需要的输入参数（你要准备什么）

你可以把本项目理解成：**输入“位移场 displacement”（珠子/特征点的位移），输出“牵引力 traction”（细胞对基底的力）**。

### 1) 运行入口（你从哪里开始）

- 在 Matlab 命令行输入：`TF_reconstruction`
- 会打开一个 GUI（界面），首先让你填写/选择输入数据和材料参数，然后选择计算方法：
  - **Regularization**：传统的“正则化 FTTC”，需要你手动给一个正则化参数
  - **Bayesian regularization**：贝叶斯 FTTC，会自动估计最合适的正则化参数（但需要噪声方差信息）

### 2) 必填输入：一个 `.mat` 文件（位移数据文件）

GUI 里你必须选择一个 Matlab 数据文件（`.mat`），该文件里必须包含一个结构体，名字必须叫：

- **`input_data`**

并且至少要有下面这个字段：

- **`input_data.displacement(frame).pos`**：位移点的位置（单位：像素 pix）
  - 形状：`N x 2`
  - 含义：每行是一个点的 `(x, y)` 坐标
- **`input_data.displacement(frame).vec`**：位移向量（单位：像素 pix）
  - 形状：`N x 2`
  - 含义：每行是该点的位移 `(ux, uy)`（即从未变形到变形的位移）

其中 `frame` 是帧号（如果是时间序列/多帧数据），从 1 开始；每一帧都可以有自己的 `pos/vec`。

#### 可选输入：噪声样本（建议用于 Bayesian 方法）

如果你要用 **Bayesian regularization**，程序需要知道“测量噪声的方差”。你可以二选一：

- **方式 A（推荐）**：在输入文件里提供噪声样本：
  - **`input_data.noise(frame).pos`**：噪声样本位置（通常可不重要，主要用 vec）
  - **`input_data.noise(frame).vec`**：噪声位移向量样本（单位：pix）
  - 程序会用 `var(noise.vec(:))` 估计噪声方差
- **方式 B**：不提供 `input_data.noise`，在 GUI 里手动圈选一块“只包含噪声”的区域（ROI），程序用该区域里的位移当作噪声样本

### 3) 必填输入：材料/成像参数（在 GUI 里填写）

这些参数在 `get_data` 界面里填写，含义如下：

- **Young's modulus（杨氏模量，Young modulus）**：基底刚度（单位：Pa）
  - GUI 中通常以 **kPa** 输入，程序内部会乘以 1000 变成 Pa
- **Poisson's ratio（泊松比）**：`0 < ν <= 0.5`
- **Micrometer per pixel（像素尺寸）**：1 像素对应多少微米（单位：µm/pix）
- **Depth of z-plane（z 平面深度）**：测量平面距离凝胶表面的深度（单位：µm，要求 >= 0）
  - 很多常见情况可用 `0`

### 4) 方法相关参数（Regularization / Bayesian 各自需要什么）

两种方法都会用到：

- **Mesh size / meshsize（网格间距）**：把离散位移插值到规则网格时的网格间隔（单位：pix）
  - 你可以理解为：牵引力结果的“分辨率/网格粗细”

仅 **Regularization** 需要：

- **Regularization parameter / regparam（正则化参数）**：一个 >= 0 的数
  - 越大一般会让结果更“平滑”，但也可能抹掉细节

仅 **Bayesian regularization** 需要：

- **Noise source（噪声来源）**：来自 `input_data.noise` 或手动 ROI
  - 程序会计算每一帧的 `beta = 1 / var(noise_sample)`
  - 然后自动得到最优正则化参数 `L`

### 5) 可选输入：细胞图像文件夹（仅用于预览叠加显示）

GUI 里可以选择一个包含细胞图像的文件夹（支持 `*.tif*` / `*.jpg*`），主要用于：

- 在预览界面把牵引力矢量叠加到图像上方便观察

不提供图像也可以做计算（只是不显示背景图）。

---

## 中文：输出是什么（程序会生成哪些结果）

不论你选哪种方法，程序都会在**输入位移文件所在目录**保存一个结果文件：

- Regularization 方法：`Reg-FTTC_results_DD-MM-YY.mat`
- Bayesian 方法：`Bay-FTTC_results_DD-MM-YY.mat`

结果文件里固定包含两个变量：

### 1) `TFM_results`（每一帧的计算结果）

`TFM_results(frame)` 是结构体数组，常见字段如下：

- **`pos`**：规则网格上每个网格点的位置（单位：pix）
  - 形状：`(i_max*j_max) x 2`
- **`traction`**：每个网格点的牵引力向量（已按杨氏模量缩放到真实刚度）
  - 形状：`(i_max*j_max) x 2`
- **`traction_magnitude`**：牵引力大小（模长）
  - 形状：`(i_max*j_max) x 1`
- **`displacement`**：插值到网格后的位移向量（单位：pix）
  - 形状：`(i_max*j_max) x 2`
- **`energy`**：应变能（strain energy），一个标量
  - 形状：`1 x 1`
  - 说明：用于描述这一帧整体“做功/能量”大小（具体物理单位与输入单位/换算有关）

注意：如果某一帧位移数据为空/太少，程序会跳过该帧，`TFM_results(frame)` 可能不存在或为空。

### 2) `TFM_settings`（本次计算用到的设置）

这是一个结构体，常见字段如下：

- **`young`**：杨氏模量（Pa）
- **`poisson`**：泊松比
- **`micrometer_per_pix`**：像素尺寸（µm/pix）
- **`meshsize`**：网格间距（pix）
- **`zdepth`**：z 深度（µm）
- **`i_max` / `j_max`**：网格尺寸
- **`regularization_parameter`**
  - Regularization 方法：一个数（你手动输入的 `regparam`）
  - Bayesian 方法：每一帧一个 `L`（向量）
- **`type_noise`**（仅 Bayesian 方法）：噪声来源说明（来自输入文件或手动 ROI）

---

## 给“完全不想用 GUI”的同学：命令行最小输入/输出（可选）

仓库里有一个例子脚本：`Easy_to_use_TFM_script_example.m`，展示了如何直接从命令行跑。

其中最关键的“牵引力计算函数”是：

- `reg_fourier_TFM(Ftux, Ftuy, L, E, s, cluster_size, i_max, j_max, grid_mat, pix_durch_my, zdepth)`
  - **输入**：傅里叶空间下的位移（`Ftux/Ftuy`）、正则化参数 `L`、材料参数 `E/ν`、网格参数等
  - **输出**：`pos`、`traction`、`traction_magnitude`，以及傅里叶空间下的牵引力 `Ftfx/Ftfy`

如果你希望我帮你把“你自己的 `.mat` 位移数据”检查一遍是否符合 `input_data` 格式，你把你的文件字段结构（或 `whos -file xxx.mat` 的输出）发我，我可以直接告诉你缺什么、怎么改。


Yunfei Huang and Benedikt Sabass, 2019.


References: 

a) Y. Huang et al. Sci. Rep., 2019, vol. 9, pp. 1–16. 
https://www.nature.com/articles/s41598-018-36896-x

b) Y. Huang, G. Gompper, B. Sabass. 2019, submitted. 
