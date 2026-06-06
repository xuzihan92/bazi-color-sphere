"""
八字色彩 · 后天八卦双螺旋球体 3D可视化
v3.0 验证脚本
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')  # 非交互式后端
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Line3DCollection
import matplotlib.patches as mpatches

class HoutianBaguaSpiralViz:
    """后天八卦双螺旋3D可视化"""
    
    def __init__(self, axis_tilt=23.5, n_turns=1.0, k_pitch=0.3):
        self.axis_tilt = np.radians(axis_tilt)
        self.n_turns = n_turns
        self.k_pitch = k_pitch
        self.R = 1.0
        
        # 中轴方向：倾斜于Z轴，在XZ平面内
        self.axis_dir = np.array([
            np.sin(self.axis_tilt),
            0,
            np.cos(self.axis_tilt)
        ])
        
        # 构建正交基
        self._build_basis()
        
        # 九宫定义（简化球坐标）
        self.bagua = {
            1: {"name": "坎", "wuxing": "水", "pos": self._spherical_to_cartesian(1.0, np.pi, 0)},
            2: {"name": "坤", "wuxing": "土", "pos": self._spherical_to_cartesian(0.8, 3*np.pi/4, np.pi/4)},
            3: {"name": "震", "wuxing": "木", "pos": self._spherical_to_cartesian(1.0, np.pi/2, 0)},
            4: {"name": "巽", "wuxing": "木", "pos": self._spherical_to_cartesian(0.9, np.pi/3, np.pi/6)},
            5: {"name": "中", "wuxing": "土", "pos": np.array([0.0, 0.0, 0.0])},
            6: {"name": "乾", "wuxing": "金", "pos": self._spherical_to_cartesian(0.9, 2*np.pi/3, -np.pi/6)},
            7: {"name": "兑", "wuxing": "金", "pos": self._spherical_to_cartesian(1.0, np.pi/2, np.pi)},
            8: {"name": "艮", "wuxing": "土", "pos": self._spherical_to_cartesian(0.8, np.pi/4, -3*np.pi/4)},
            9: {"name": "离", "wuxing": "火", "pos": self._spherical_to_cartesian(1.0, 0, 0)},
        }
    
    def _build_basis(self):
        """构建中轴坐标系的正交基"""
        self.z_p = self.axis_dir
        
        # X'轴：垂直于Z'且在水平面有分量
        temp = np.array([0, 0, 1])
        self.x_p = np.cross(temp, self.z_p)
        if np.linalg.norm(self.x_p) < 1e-10:
            self.x_p = np.array([1, 0, 0])
        else:
            self.x_p /= np.linalg.norm(self.x_p)
        
        # Y' = Z' × X'
        self.y_p = np.cross(self.z_p, self.x_p)
        self.y_p /= np.linalg.norm(self.y_p)
    
    def _spherical_to_cartesian(self, r, theta, phi):
        """球坐标转直角坐标"""
        x = r * np.sin(theta) * np.cos(phi)
        y = r * np.sin(theta) * np.sin(phi)
        z = r * np.cos(theta)
        return np.array([x, y, z])
    
    def _axis_to_cartesian(self, r, theta_p, phi_p):
        """中轴球坐标转标准直角坐标"""
        # 在中轴坐标系中的直角坐标
        x_p = r * np.sin(theta_p) * np.cos(phi_p)
        y_p = r * np.sin(theta_p) * np.sin(phi_p)
        z_p = r * np.cos(theta_p)
        
        # 转回标准坐标系
        P_axis = np.array([x_p, y_p, z_p])
        P_std = x_p * self.x_p + y_p * self.y_p + z_p * self.z_p
        return P_std
    
    def generate_yang_spiral(self, n_points=200):
        """生成阳螺旋 坎1→坤2→震3→巽4→中5"""
        t = np.linspace(0, 1, n_points)
        points = []
        
        for ti in t:
            r = self.R * (1 - ti)
            phi_p = 2 * np.pi * self.n_turns * ti
            theta_p = np.pi/2 - self.k_pitch * ti * np.pi/4
            
            p = self._axis_to_cartesian(r, theta_p, phi_p)
            points.append(p)
        
        return np.array(points)
    
    def generate_yin_spiral(self, n_points=200):
        """生成阴螺旋 中5→乾6→兑7→艮8→离9→坎1"""
        t = np.linspace(0, 1, n_points)
        points = []
        
        for ti in t:
            r = self.R * ti
            phi_p = 2 * np.pi * self.n_turns * ti + np.pi
            theta_p = np.pi/2 + self.k_pitch * ti * np.pi/4
            
            p = self._axis_to_cartesian(r, theta_p, phi_p)
            points.append(p)
        
        return np.array(points)
    
    def plot(self, save_path=None):
        """绘制3D双螺旋图"""
        fig = plt.figure(figsize=(14, 12))
        ax = fig.add_subplot(111, projection='3d')
        
        # 生成螺旋
        yang_pts = self.generate_yang_spiral(300)
        yin_pts = self.generate_yin_spiral(300)
        
        # 绘制阳螺旋（红色渐变）
        for i in range(len(yang_pts)-1):
            alpha = 1.0 - i / len(yang_pts)
            ax.plot3D(yang_pts[i:i+2, 0], yang_pts[i:i+2, 1], yang_pts[i:i+2, 2],
                     color=(1.0, 0.2, 0.2), alpha=alpha, linewidth=2)
        
        # 绘制阴螺旋（蓝色渐变）
        for i in range(len(yin_pts)-1):
            alpha = i / len(yin_pts)
            ax.plot3D(yin_pts[i:i+2, 0], yin_pts[i:i+2, 1], yin_pts[i:i+2, 2],
                     color=(0.2, 0.4, 1.0), alpha=alpha, linewidth=2)
        
        # 绘制半透明球面
        u = np.linspace(0, 2*np.pi, 30)
        v = np.linspace(0, np.pi, 30)
        x_s = np.outer(np.cos(u), np.sin(v))
        y_s = np.outer(np.sin(u), np.sin(v))
        z_s = np.outer(np.ones(np.size(u)), np.cos(v))
        ax.plot_surface(x_s, y_s, z_s, alpha=0.08, color='lightgray', 
                       rstride=2, cstride=2, linewidth=0)
        
        # 绘制中轴
        axis_start = -1.2 * self.axis_dir
        axis_end = 1.2 * self.axis_dir
        ax.plot3D([axis_start[0], axis_end[0]], 
                 [axis_start[1], axis_end[1]], 
                 [axis_start[2], axis_end[2]], 
                 'k--', linewidth=1.5, alpha=0.5, label='中轴(巽4→中5→乾6)')
        
        # 标记九宫位置
        colors_wuxing = {
            "木": "green",
            "火": "red", 
            "土": "orange",
            "金": "gold",
            "水": "blue"
        }
        
        for num, data in self.bagua.items():
            pos = data["pos"]
            color = colors_wuxing.get(data["wuxing"], "gray")
            
            ax.scatter(*pos, c=color, s=150, marker='o', edgecolors='black', linewidths=1.5, zorder=5)
            
            # 偏移标签避免重叠
            offset = 0.08
            ax.text(pos[0]+offset, pos[1]+offset, pos[2]+offset, 
                   f"{num}{data['name']}", fontsize=11, fontweight='bold',
                   color='darkred' if num == 5 else 'black')
        
        # 设置坐标轴
        ax.set_xlim([-1.3, 1.3])
        ax.set_ylim([-1.3, 1.3])
        ax.set_zlim([-1.3, 1.3])
        ax.set_xlabel('X (春分→秋分)', fontsize=11)
        ax.set_ylabel('Y (冬至→夏至)', fontsize=11)
        ax.set_zlabel('Z (北极↑)', fontsize=11)
        
        # 标题
        ax.set_title('后天八卦双螺旋球体 v3.0\n中轴倾斜23.5° | 阳螺旋(红):坎1→中5 | 阴螺旋(蓝):中5→坎1', 
                    fontsize=13, fontweight='bold', pad=20)
        
        # 图例
        red_line = mpatches.Patch(color=(1.0, 0.2, 0.2), label='阳螺旋 坎1→坤2→震3→巽4→中5')
        blue_line = mpatches.Patch(color=(0.2, 0.4, 1.0), label='阴螺旋 中5→乾6→兑7→艮8→离9→坎1')
        ax.legend(handles=[red_line, blue_line], loc='upper left', fontsize=9)
        
        # 设置等比例
        ax.set_box_aspect([1,1,1])
        
        # 添加网格
        ax.grid(True, alpha=0.3)
        
        if save_path:
            plt.savefig(save_path, dpi=200, bbox_inches='tight', facecolor='white')
            print(f"图片已保存到: {save_path}")
        
        plt.show()
        return fig, ax

if __name__ == "__main__":
    viz = HoutianBaguaSpiralViz(axis_tilt=23.5, n_turns=1.0, k_pitch=0.4)
    viz.plot(save_path="houtian_bagua_spiral_v3.png")
