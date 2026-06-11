“””
BIS 前向算子矩阵构建与（可选）Tikhonov 正则反演。

离散网格 → 解析积分消奇异 → 线性系统 u = A t。
solve_tikhonov 可作为 TFM 反演的起点。
“””

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional, Tuple

import numpy as np

from modules.displacement import compute_displacement_from_force_component_si


@dataclass(frozen=True)
class BISSquareGrid:
    """
    BIS离散网格（方形单元）。

    - 牵引应力 t_x, t_y 假设在每个 cell 内常数（Pa）
    - cell 以中心点表示，边长 cell_size_px（pixel）
    """

    field_width_px: float
    field_height_px: float
    boundary_px: float
    spacing_px: float
    cell_size_px: float
    x_centers_px: np.ndarray  # shape (Nx,)
    y_centers_px: np.ndarray  # shape (Ny,)

    @property
    def shape(self) -> Tuple[int, int]:
        return (len(self.y_centers_px), len(self.x_centers_px))  # (Ny, Nx)

    @property
    def n_cells(self) -> int:
        ny, nx = self.shape
        return int(nx * ny)

    def mesh_centers(self) -> Tuple[np.ndarray, np.ndarray]:
        Xc, Yc = np.meshgrid(self.x_centers_px, self.y_centers_px)
        return Xc, Yc


def create_bis_square_grid(
    field_width_px: float,
    field_height_px: float,
    boundary_px: float,
    spacing_px: float,
    cell_size_px: Optional[float] = None,
) -> BISSquareGrid:
    """
    创建BIS方形离散网格（单元中心点落在规则网格上）。

    常见做法：cell_size_px = spacing_px（每个采样间距一个单元）。
    """
    if cell_size_px is None:
        cell_size_px = float(spacing_px)

    x_centers = np.arange(boundary_px, field_width_px - boundary_px + spacing_px, spacing_px, dtype=float)
    y_centers = np.arange(boundary_px, field_height_px - boundary_px + spacing_px, spacing_px, dtype=float)

    return BISSquareGrid(
        field_width_px=float(field_width_px),
        field_height_px=float(field_height_px),
        boundary_px=float(boundary_px),
        spacing_px=float(spacing_px),
        cell_size_px=float(cell_size_px),
        x_centers_px=x_centers,
        y_centers_px=y_centers,
    )


def pack_traction_fields(tx_pa: np.ndarray, ty_pa: np.ndarray) -> np.ndarray:
    """
    把 (tx,ty) 两个2D场打包成 t 向量，列顺序为 [tx_flat, ty_flat]。
    """
    if tx_pa.shape != ty_pa.shape:
        raise ValueError(f"tx_pa 与 ty_pa 形状必须一致，当前: {tx_pa.shape} vs {ty_pa.shape}")
    return np.concatenate([tx_pa.ravel(), ty_pa.ravel()]).astype(float, copy=False)


def unpack_traction_vector(t: np.ndarray, grid: BISSquareGrid) -> Tuple[np.ndarray, np.ndarray]:
    """
    把 t 向量拆成 (tx,ty) 两个2D场，形状为 grid.shape。
    """
    n = grid.n_cells
    t = np.asarray(t).reshape(-1)
    if t.size != 2 * n:
        raise ValueError(f"t 长度应为 2*{n}，当前: {t.size}")
    tx = t[:n].reshape(grid.shape)
    ty = t[n:].reshape(grid.shape)
    return tx, ty


def build_bis_operator_matrix(
    X_obs_px: np.ndarray,
    Y_obs_px: np.ndarray,
    grid: BISSquareGrid,
    E_pa: float,
    nu: float,
    pixel_size_um: float,
    dtype=np.float32,
    progress_cb: Optional[Callable[[int, int], None]] = None,
) -> np.ndarray:
    """
    构建 BIS 前向算子矩阵 A，使得：
        u_vec = A @ t_vec

    其中：
    - u_vec = [u_x_flat, u_y_flat]，单位 pixel
    - t_vec = [t_x_flat, t_y_flat]，单位 Pa
    - A 的单位是 (pixel / Pa)

    维度：
    - N = X_obs_px.size（采样点数量）
    - M = grid.n_cells（单元数量）
    - A shape = (2N, 2M)

    性能提示：
    - 500×500, boundary=40, spacing=10 → N≈1849, M≈1849
    - A 大小约 3698×3698（float32约 52MB）
    """
    X_obs_px = np.asarray(X_obs_px, dtype=float)
    Y_obs_px = np.asarray(Y_obs_px, dtype=float)
    if X_obs_px.shape != Y_obs_px.shape:
        raise ValueError("X_obs_px 与 Y_obs_px 的形状必须一致")

    n_obs = int(X_obs_px.size)
    n_cells = grid.n_cells
    A = np.zeros((2 * n_obs, 2 * n_cells), dtype=dtype)

    Xc, Yc = grid.mesh_centers()
    half_size_px = grid.cell_size_px / 2.0

    # 单位牵引应力响应：p=1 Pa
    unit_p = 1.0

    # 遍历每个cell，计算其对所有采样点的响应
    # - x方向牵引：direction='x'，填入 A[:, j]
    # - y方向牵引：direction='y'，填入 A[:, M+j]
    for j, (xc, yc) in enumerate(zip(Xc.ravel(), Yc.ravel())):
        if progress_cb is not None:
            progress_cb(j + 1, n_cells)

        # traction in x
        ux_x, uy_x = compute_displacement_from_force_component_si(
            X_obs_px,
            Y_obs_px,
            (float(xc), float(yc)),
            half_size_px,
            unit_p,
            float(E_pa),
            float(nu),
            float(pixel_size_um),
            direction="x",
        )
        A[:n_obs, j] = ux_x.reshape(-1)
        A[n_obs:, j] = uy_x.reshape(-1)

        # traction in y
        ux_y, uy_y = compute_displacement_from_force_component_si(
            X_obs_px,
            Y_obs_px,
            (float(xc), float(yc)),
            half_size_px,
            unit_p,
            float(E_pa),
            float(nu),
            float(pixel_size_um),
            direction="y",
        )
        col = n_cells + j
        A[:n_obs, col] = ux_y.reshape(-1)
        A[n_obs:, col] = uy_y.reshape(-1)

    return A


def apply_bis_operator_matrix(
    A: np.ndarray,
    t_vec: np.ndarray,
    obs_shape: Tuple[int, int],
) -> Tuple[np.ndarray, np.ndarray]:
    """
    用 A @ t 得到 (u_x, u_y)，并恢复为 obs_shape。
    """
    t_vec = np.asarray(t_vec).reshape(-1)
    u_vec = A @ t_vec

    n_obs = int(np.prod(obs_shape))
    if u_vec.size != 2 * n_obs:
        raise ValueError("A 与 obs_shape 不匹配：输出长度不等于 2*Nobs")

    u_x = u_vec[:n_obs].reshape(obs_shape)
    u_y = u_vec[n_obs:].reshape(obs_shape)
    return u_x, u_y


def solve_tikhonov(
    A: np.ndarray,
    u_x: np.ndarray,
    u_y: np.ndarray,
    lam: float,
) -> np.ndarray:
    """
    （可选）标准零阶Tikhonov正则：
        min_t ||A t - u||^2 + lam^2 ||t||^2

    返回:
        t_vec = [t_x_flat, t_y_flat] (Pa)
    """
    if lam < 0:
        raise ValueError("lam 必须非负")

    u = np.concatenate([u_x.reshape(-1), u_y.reshape(-1)]).astype(float, copy=False)
    A = np.asarray(A)

    # 正规方程：(A^T A + lam^2 I) t = A^T u
    AtA = A.T @ A
    rhs = A.T @ u
    if lam > 0:
        AtA = AtA + (lam ** 2) * np.eye(AtA.shape[0], dtype=AtA.dtype)

    t = np.linalg.solve(AtA, rhs)
    return t


