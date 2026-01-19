# 代码修复

原代码中存在不能运行、以及原作者遗漏的部分，在此进行了合理的修复。

## 修复 vectorialPSF 报错

Save 会触发 `MovieData.sanityCheck()`，其中会对每个 Channel 做 `sanityCheck()`；而 Channel 在 psfSigma_ 为空时会调用 `calculatePSFSigma()`，进而调用 `getGaussianPSFsigma()`，里面会用到 `vectorialPSF()` 生成 PSF。
原代码里 确实带了 vectorialPSF（在 algorithms/matlab/u-inferforce-master/software/mex/ 下面有 vectorialPSF.mexw64 等），但没有把 software/mex 自动加入 MATLAB path，所以在保存时调用 vectorialPSF 就会报“未定义…”

## 修复 “未定义与 'double' 类型的输入参数相对应的函数 parfor_progress”
代码在执行 `parfor_progress(n)`（这里 n 是 double，比如 nFrames/nPoints）时，MATLAB 找不到名为 parfor_progress 的函数（或找到了但不是可调用函数），所以 Step 2 displacement field calculation 直接中断。

fix:把所有调用点改成：只有当 parfor_progress 在 path 上确实存在时才调用，否则跳过进度条，不影响算法运行。

## 修复减内存机制 divideConquer
在 Step 4: Force Field Calculation 里，算法需要分配/持有非常大的数组或矩阵（典型是 FastBEM 里的前向矩阵 M、以及 useLcurve=true 时为 L-curve 扫描保存多组解），结果超出了你当前 MATLAB 能用的 RAM（或连续内存块）容量，容易出现“内存不足”的错误。

解决方法：
- 关闭 L-curve：把 useLcurve 设为 false，手动给一个 regParam（比如先用默认 1e-4 或稍大一点）。
- 这是最常见的爆内存来源之一。
- 降低前向求解网格密度：把 meshPtsFwdSol 从 4096 降到 2048 或 1024。
- 缩小 ROI / 让位移场更稀疏：ROI 越大、位移点越多，矩阵越大。
- 换更省内存的方法：如果 GUI 允许，试试 `method='FTTC'`（通常比 BEM 省内存，但物理模型和边界假设不同）。

同时在原代码中有一个减内存机制 `divideConquer`（把网格分块算，降低峰值内存），但之前被硬编码成 1。
修改：
在 `ForceFieldCalculationProcess.getDefaultParams()` 里加入 `funParams.divideConquer = 1`
在 calculateMovieForceField.m 里 不再强制覆盖 `divideConquer=1`，允许将其修改成 9（3×3 分块）等来降低峰值内存