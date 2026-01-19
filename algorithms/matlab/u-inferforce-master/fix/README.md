

## 修复 vectorialPSF 报错

Save 会触发 MovieData.sanityCheck()，其中会对每个 Channel 做 sanityCheck()；而 Channel 在 psfSigma_ 为空时会调用 calculatePSFSigma()，进而调用 getGaussianPSFsigma()，里面会用到 vectorialPSF() 生成 PSF。
原代码里 确实带了 vectorialPSF（在 algorithms/matlab/u-inferforce-master/software/mex/ 下面有 vectorialPSF.mexw64 等），但没有把 software/mex 自动加入 MATLAB path，所以在保存时调用 vectorialPSF 就会报“未定义…”