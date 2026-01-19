

## 修复 vectorialPSF 报错

Save 会触发 MovieData.sanityCheck()，其中会对每个 Channel 做 sanityCheck()；而 Channel 在 psfSigma_ 为空时会调用 calculatePSFSigma()，进而调用 getGaussianPSFsigma()，里面会用到 vectorialPSF() 生成 PSF。
原代码里 确实带了 vectorialPSF（在 algorithms/matlab/u-inferforce-master/software/mex/ 下面有 vectorialPSF.mexw64 等），但没有把 software/mex 自动加入 MATLAB path，所以在保存时调用 vectorialPSF 就会报“未定义…”

## 修复 “未定义与 'double' 类型的输入参数相对应的函数 parfor_progress”
代码在执行 parfor_progress(n)（这里 n 是 double，比如 nFrames/nPoints）时，MATLAB 找不到名为 parfor_progress 的函数（或找到了但不是可调用函数），所以 Step 2 displacement field calculation 直接中断。

fix:把所有调用点改成：只有当 parfor_progress 在 path 上确实存在时才调用，否则跳过进度条，不影响算法运行。