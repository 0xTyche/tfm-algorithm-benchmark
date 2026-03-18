A standardized and reproducible benchmark for Traction Force Microscopy (TFM) algorithms.

## intro

This repository is designed to maintain and compare different Traction Force Microscopy (TFM) algorithms within a unified and standardized framework. It provides consistent data interfaces, evaluation pipelines, and reproducible workflows for benchmarking multiple TFM implementations.

Standardized synthetic datasets with known ground truth are included to enable fair and quantitative comparison of various TFM methods.


## Project Structure

```text
tfm-algorithm-benchmark/
│
├── README.md
├── LICENSE
├── .gitignore
│
├── docs/                         # 文档与综述（核心）
│   ├── overview.md               # TFM 方法总览 & 分类
│   ├── comparison_table.md       # 各算法横向对比表
│   └── terminology.md            # 常用术语/符号/假设说明
│
├── algorithms/                   # 各类 TFM 算法整理（核心）
│   ├── matlab/
│   │   ├── u-inferforce/
│   │   │   ├── README.md
│   │   │   ├── code/
│   │   │   ├── paper.md
│   │   │   ├── language.md
│   │   │   ├── github.md
│   │   │   └── summary.md
│   │   │
│   │   ├── Easy-to-use_TFM_package/
|   |   |   ├── documentation/
    |   |   |   └── User_Manual_Easy-To-Use_TFM_software.pdf
│   │   │   ├── code/
│   │   │   ├── paper.md
│   │   │   ├── language.md
│   │   │   ├── github.md
│   │   │   └── summary.md
│   │   │
│   │   ├── TFMLAB/
│   │   │   ├── README.md
│   │   │   ├── code/
│   │   │   ├── paper.md
│   │   │   ├── language.md
│   │   │   ├── github.md
│   │   │   └── summary.md
│   │   │
│   │   ├── TFMLAB/
│   │   │   ├── README.md
│   │   │   ├── code/
│   │   │   ├── paper.md
│   │   │   ├── language.md
│   │   │   ├── github.md
│   │   │   └── summary.md
│   │
│   ├── python/
│   │   ├── pyTFM/
│   │   │   ├── code/
│   │   │   ├── README.md
│   │   │   ├── paper.md
│   │   │   ├── language.md
│   │   │   ├── github.md
│   │   │   └── summary.md
│   │
│   ├── cpp/
│   │   ├── cellogram/
│   │   │   ├── code
│   │   │   ├── README.md
│   │   │   ├── paper.md
│   │   │   ├── language.md
│   │   │   ├── github.md
│   │   │   └── summary.md
│   │
│   └── no_code/
│       ├── imagej_tfm/
│       │   ├── paper.md
│       │   └── summary.md
│       │
│       ├── style_review_2014/
│       │   ├── paper.md
│       │   └── summary.md
│       │
│       └── jeasyTFM/
│           ├── paper.md
│           └── summary.md
│
├── datasets/                     # 标准/模拟/验证数据
│   ├── synthetic/
│   │   ├── README.md
│   │   ├── ground_truth/
│   │   └── displacement_fields/
│   │
│   ├── experimental/
│   │   ├── cTFM_confocal/
│   │   │   ├── README.md
│   │   │   └── source_link.md
│   │
│   └── benchmarks.md
│
├── evaluation/                   # 评测指标、流程与评测脚本（核心）
│   ├── metrics.md                # 指标定义：RMSE, magnitude, angle, vector error 等
│   ├── protocols.md              # 统一评测流程与输入输出规范
│   ├── visualization.md          # 可视化规范（热图、矢量场、误差图）
│   ├── evaluate_force_magnitude.py   # 评估力的大小（traction magnitude）
│   ├── evaluate_force_angle.py       # 评估力的方向角度（angle error）
│   ├── evaluate_runtime.py           # 评估算法运行速度（runtime / throughput）
│   └── evaluate_vector_field.py      # 评估力矢量（vector field error）
│
├── notes/                        # 个人/实验室经验总结（可选）
│   ├── lab_usage_notes.md        # “实验室多数同学在用的程序”
│   └── pitfalls.md               # 常见坑、参数陷阱
│
└── references/
    ├── papers.bib
    └── reading_list.md

```