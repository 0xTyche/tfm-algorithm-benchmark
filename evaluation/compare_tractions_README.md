# evaluation

该 readme 用于说明 使用 u-inferforce 的样例数据输入到 easy_to_use_tfm 的程序中，效果如何，`compare_tractions.py` 脚本用于比对两个TFM程序的输出差别

## 推荐的对比对象（数据层）

相比对比 `.fig` 图像，优先对比 **数值结果**：

- **u-inferforce**：`.../uInferforcePackage/forceField/forceField.mat`
  - 变量：`forceField( frame ).pos / .vec`（单位通常为 Pa，坐标为像素）
- **Easy-to-use TFM**（Bayesian/Regularized FTTC）：`Bay-FTTC_results_*.mat`
  - 变量：`TFM_results( frame ).pos / .traction`（单位通常为 Pa，坐标为像素）

## 脚本

- `compare_tractions.py`
  - 将两种格式统一为“在同一组 (x,y) 点上的牵引力向量”，再计算对比指标：
    - RMSE（Tx,Ty）、RMSE（|T|）
    - Cosine similarity（方向一致性）
    - Angle error（角度误差，度）
    - 最优比例因子（仅用于检查刚度/尺度不一致导致的整体缩放差异）
  - 可选输出 **二维概率密度图（2D density）**：
    - 牵引力模长：\(|T|_{u\text{-}inferforce}\) vs \(|T|_{easy}\)
    - 牵引力方向：\(\theta_{u\text{-}inferforce}\) vs \(\theta_{easy}\)
    - 角度误差 vs 力大小：\(|T|_{u\text{-}inferforce}\) vs angle error

## 用法（示例）

```bash
python evaluation/compare_tractions.py ^
  --uinferforce-forcefield "datasets/u-inferforce-master-datasets/Results/uInferforcePackage/forceField/forceField.mat" ^
  --easy-bay "datasets/Standard data(u-inferforce to easy to use tfm)/Bay-FTTC_results_20-01-26.mat" ^
  --out "datasets/Standard data(u-inferforce to easy to use tfm)/traction_compare.json" ^
  --plots-dir "datasets/Standard data(u-inferforce to easy to use tfm)/plots" ^
  --log-density
```

