import os
import re
import sys
import copy
import numpy as np
from tqdm import tqdm
import matplotlib.pyplot as plt
import matplotlib.lines as mlines
from numpy.linalg import inv
from numpy import linalg as LA
from src.utils.utils import check_dir, ActionMode, PlotMode
from matplotlib.collections import LineCollection

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def legend_without_duplicate_labels(ax):
    handles, labels = ax.get_legend_handles_labels()
    unique = [(h, l) for i, (h, l) in enumerate(zip(handles, labels)) if l not in labels[:i]]
    ax.legend(*zip(*unique), fontsize="7.3", loc='best')
    # ax.legend(*zip(*unique), fontsize="15", loc='best')


class FigPlotter:
    def __init__(self, plotter_cfg):
        self.params = plotter_cfg
        self.phase_dir = plotter_cfg.phase.save_dir
        self.trajectory_dir = plotter_cfg.trajectory.save_dir

        self.check_all_dir(plotter_cfg.phase.plot, plotter_cfg.trajectory.plot)

        # For live plot
        self.last_live_state = None
        self.last_live_action = 0
        self.last_live_action_mode = None
        self.last_live_energy = 0

        self.line_collections = []

    def reset_live_variables(self):
        self.last_live_state = []
        self.last_live_action = 0
        self.last_live_action_mode = None
        self.last_live_energy = 0

    def check_all_dir(self, phase_plot, trajectory_plot):
        if phase_plot:
            check_dir(self.phase_dir)

        if trajectory_plot:
            check_dir(self.trajectory_dir)

    def change_dir(self, old_dir: str, new_dir: str):
        try:
            pattern = rf'\b{old_dir}\b'
            self.phase_dir = re.sub(pattern, new_dir, self.phase_dir)
            self.trajectory_dir = re.sub(pattern, new_dir, self.trajectory_dir)
            self.check_all_dir(phase_plot=self.params.phase.plot,
                               trajectory_plot=self.params.trajectory.plot)
        except:
            raise RuntimeError("Failed to change the plotter existing directory")

    def phase_portrait(self, state_list, action_mode_list, x_set, theta_set, epsilon, p_mat, idx):
        # Figure name
        fig_name = f"{self.phase_dir}/phase{idx}.png"
        print(f"Plotting Phase to: {fig_name}...")

        # Phase
        self.plot_phase(state_list=state_list, action_mode_list=action_mode_list, idx=idx)

        # Safety envelope
        self.plot_envelope(p_mat=p_mat, epsilon=epsilon)

        # Safety set
        # self.plot_safety_set(x_set=x_set, theta_set=theta_set)

        # plt.title(f"Inverted Pendulum Phase ($f = {freq} Hz$)", fontsize=14)
        # plt.xlabel('x (m)', fontsize=18)
        # plt.ylabel('$\\theta$ (rad)', fontsize=18)
        plt.xlabel('x', fontsize=18)
        plt.ylabel('$\\theta$', fontsize=18)
        # plt.legend(loc="lower left", markerscale=4, handlelength=1.2, handletextpad=0.5, bbox_to_anchor=(0.05, 0.05),
        #            fontsize=10)
        plt.savefig(fig_name)

        print(f"Successfully plot phase: {fig_name}")
        plt.close()

    def plot_phase(self, state_list, action_mode_list, idx, plot_mode=PlotMode.POSITION):
        assert len(state_list) == len(action_mode_list)

        states = np.array(state_list)
        x, x_dot, theta, theta_dot = states[:, 0], states[:, 1], states[:, 2], states[:, 3]

        if plot_mode == PlotMode.POSITION:
            phases = np.vstack((x, theta)).T
        elif plot_mode == PlotMode.VELOCITY:
            phases = np.vstack(([x_dot, theta_dot])).T
        else:
            raise NotImplementedError(f"Unrecognized plot mode: {plot_mode}")
        # eq points
        # if plot_eq and eq_point is not None:
        #     print(f"eq point: {eq_point}")
        #     plt.plot(eq_point[0], eq_point[2], '*', color=[0.4660, 0.6740, 0.1880], markersize=8)
        student_cnt = 0
        teacher_cnt = 0
        for i in range(len(phases) - 1):
            if action_mode_list[i] == ActionMode.STUDENT:
                plt.plot(phases[i][0], phases[i][1], '.', color=[0, 0.4470, 0.7410],
                         markersize=2)  # student phases
                student_cnt += 1
            elif action_mode_list[i] == ActionMode.TEACHER:
                plt.plot(phases[i][0], phases[i][1], 'r.', markersize=2)  # teacher phases
                teacher_cnt += 1
            else:
                raise RuntimeError(f"Unrecognized action mode: {action_modes[i]}")

        # Add label
        # h1, = plt.plot(phases[-1][0], phases[-1][1], 'kx', label="End State", markersize=1.5)
        # h2, = plt.plot(phases[-1][0], phases[-1][1], 'k.', label="Initial State", markersize=2)
        h3, = plt.plot(phases[-1][0], phases[-1][1], '-', color=[0, 0.4470, 0.7410], label="HP Student", markersize=2)
        h4, = plt.plot(phases[-1][0], phases[-1][1], 'r-', label="HA Teacher", markersize=2)

        # Add marker for initial/end state
        h5, = plt.plot(phases[0][0], phases[0][1], 'ko', markersize=7, mew=1.2)  # initial state
        h6, = plt.plot(phases[-1][0], phases[-1][1], 'k*', markersize=11, mew=1.2)  # end state
        plt.legend(loc='upper right', fontsize=12)

        # # 读取并打印文件内容
        # with open('count.txt', 'a+') as file:
        #     file.write(f"episode {idx}: ha_teacher: {teacher_cnt}, hp_student: {student_cnt}\n")
        #     file.close()

    def plot_trajectory(self, state_list, action_list, action_mode_list, energy_list, x_set, theta_set, action_set,
                        freq, fig_idx):
        # Figure name
        fig_name = f'{self.trajectory_dir}/trajectory{fig_idx}.png'
        print(f"Plotting Trajectory to: {fig_name}...")

        x_l, x_h = x_set
        th_l, th_h = theta_set
        f_l, f_h = action_set
        x_ticks = np.linspace(x_l, x_h, 5)
        th_ticks = np.linspace(th_l, th_h, 5)
        f_ticks = np.linspace(f_l, f_h, 5)

        n1 = len(state_list)
        n2 = len(action_list)
        n3 = len(action_mode_list)
        n4 = len(energy_list)
        assert n1 == n2
        assert n2 == n3
        assert n3 == n4

        trajectories = np.asarray(state_list)
        fig, axes = plt.subplots(3, 2, figsize=(12, 6))  # Create a 2x2 subplot grid
        fig.suptitle(f'Inverted Pendulum Trajectories ($f = {freq} Hz$)', fontsize=11, ha='center', y=0.97)

        for i in range(n1 - 1):
            self.line_segment(axes=axes,
                              state1=trajectories[i],
                              state2=trajectories[i + 1],
                              action1=action_list[i],
                              action2=action_list[i + 1],
                              energy1=energy_list[i],
                              energy2=energy_list[i + 1],
                              action_mode=action_mode_list[i],
                              i=i)

        # Add legend and label
        self.legend_and_label(axes, x_ticks, th_ticks, f_ticks)

        plt.tight_layout()  # Adjust spacing between subplots
        plt.savefig(fig_name, dpi=150)
        plt.close(fig)
        print(f"Successfully plot trajectory: {fig_name}")

    @staticmethod
    def legend_and_label(axes, x_ticks, th_ticks, f_ticks):
        # Add label and title (x)
        axes[0, 0].set_yticks(x_ticks)
        axes[0, 0].set_ylabel("x (m)")
        axes[0, 0].add_line(mlines.Line2D([], [], color=[0, 0.4470, 0.7410], linestyle='-', label='HPC'))
        axes[0, 0].add_line(mlines.Line2D([], [], color='red', linestyle='-', label='HAC'))
        legend_without_duplicate_labels(axes[0, 0])

        # Add label and title (x_dot)
        # axes[0, 1].set_yticks(np.linspace(-3, 3, 5))
        axes[0, 1].set_ylabel(r"$\dot{x}$ (m/s)")
        axes[0, 1].add_line(mlines.Line2D([], [], color=[0, 0.4470, 0.7410], linestyle='-', label='HPC'))
        axes[0, 1].add_line(mlines.Line2D([], [], color='red', linestyle='-', label='HAC'))
        legend_without_duplicate_labels(axes[0, 1])

        # Add label and title (theta)
        axes[1, 0].set_yticks(th_ticks)
        axes[1, 0].set_ylabel('$\\theta$ (rad)')
        axes[1, 0].add_line(mlines.Line2D([], [], color=[0, 0.4470, 0.7410], linestyle='-', label='HPC'))
        axes[1, 0].add_line(mlines.Line2D([], [], color='red', linestyle='-', label='HAC'))
        legend_without_duplicate_labels(axes[1, 0])

        # Add label and title (theta_dot)
        # axes[1, 1].set_yticks(np.linspace(-4.5, 4.5, 5))
        axes[1, 1].set_ylabel(r'$\dot{\theta}$ (rad/s)')
        axes[1, 1].add_line(mlines.Line2D([], [], color=[0, 0.4470, 0.7410], linestyle='-', label='HPC'))
        axes[1, 1].add_line(mlines.Line2D([], [], color='red', linestyle='-', label='HAC'))
        legend_without_duplicate_labels(axes[1, 1])

        # Add label and title (force)
        axes[2, 0].set_yticks(f_ticks)
        axes[2, 0].set_ylabel("force (N)")
        axes[2, 0].add_line(mlines.Line2D([], [], color=[0, 0.4470, 0.7410], linestyle='-', label='HPC'))
        axes[2, 0].add_line(mlines.Line2D([], [], color='red', linestyle='-', label='HAC'))
        legend_without_duplicate_labels(axes[2, 0])

        # Add label and title (system energy)
        # axes[2, 1].set_yticks(np.linspace(0, 3, 5))
        axes[2, 1].set_ylabel("system energy")
        axes[2, 1].add_line(mlines.Line2D([], [], color=[0, 0.4470, 0.7410], linestyle='-', label='HPC'))
        axes[2, 1].add_line(mlines.Line2D([], [], color='red', linestyle='-', label='HAC'))
        legend_without_duplicate_labels(axes[2, 1])

    @staticmethod
    def line_segment(axes, state1, state2, action1, action2, action_mode, energy1, energy2, i):
        if action_mode == ActionMode.STUDENT:
            # x
            axes[0, 0].plot([i, i + 1], [state1[0], state2[0]], '-', label='HPC', color=[0, 0.4470, 0.7410])

            # x_dot
            axes[0, 1].plot([i, i + 1], [state1[1], state2[1]], '-', label='HPC', color=[0, 0.4470, 0.7410])

            # theta
            axes[1, 0].plot([i, i + 1], [state1[2], state2[2]], '-', label='HPC', color=[0, 0.4470, 0.7410])

            # theta_dot
            axes[1, 1].plot([i, i + 1], [state1[3], state2[3]], '-', label='HPC', color=[0, 0.4470, 0.7410])

            # force/action
            axes[2, 0].plot([i, i + 1], [action1, action2], '-', label='HPC', color=[0, 0.4470, 0.7410])

            # system energy
            axes[2, 1].plot([i, i + 1], [energy1, energy2], '-', label='HPC', color=[0, 0.4470, 0.7410])

        elif action_mode == ActionMode.TEACHER:
            # x
            axes[0, 0].plot([i, i + 1], [state1[0], state2[0]], 'r-', label='HAC')

            # x_dot
            axes[0, 1].plot([i, i + 1], [state1[1], state2[1]], 'r-', label='HAC')

            # theta
            axes[1, 0].plot([i, i + 1], [state1[2], state2[2]], 'r-', label='HAC')

            # theta_dot
            axes[1, 1].plot([i, i + 1], [state1[3], state2[3]], 'r-', label='HAC')

            # force/action
            axes[2, 0].plot([i, i + 1], [action1, action2], 'r-', label='HAC')

            # system energy
            axes[2, 1].plot([i, i + 1], [energy1, energy2], 'r-', label='HAC')

        else:
            raise RuntimeError(f"Unrecognized action mode: {action_mode_list[i]}")

    @staticmethod
    def plot_safety_set(x_set=[-0.9, 0.9], theta_set=[-0.8, 0.8]):
        x_l, x_h = x_set
        th_l, th_h = theta_set

        # Safety Set
        plt.vlines(x=x_l, ymin=th_l, ymax=th_h, color='black', linewidth=2.5)
        plt.vlines(x=x_h, ymin=th_l, ymax=th_h, color='black', linewidth=2.5)
        plt.hlines(y=th_l, xmin=x_l, xmax=x_h, color='black', linewidth=2.5)
        plt.hlines(y=th_h, xmin=x_l, xmax=x_h, color='black', linewidth=2.5)

    @staticmethod
    def plot_envelope(p_mat, epsilon):
        p_mat = p_mat * 0.2  # The rendered envelope in two dimensions will be larger
        cP = p_mat

        tP = np.zeros((2, 2))
        vP = np.zeros((2, 2))

        # For velocity
        vP[0][0] = cP[1][1]
        vP[1][1] = cP[3][3]
        vP[0][1] = cP[1][3]
        vP[1][0] = cP[1][3]

        # For position
        tP[0][0] = cP[0][0]
        tP[1][1] = cP[2][2]
        tP[0][1] = cP[0][2]
        tP[1][0] = cP[0][2]

        wp, vp = LA.eig(tP)
        # wp_eps, vp_eps = LA.eig(tP / epsilon)
        wp_eps, vp_eps = LA.eig(tP / 1)
        # wp, vp = LA.eig(vP)

        theta = np.linspace(-np.pi, np.pi, 1000)

        ty1 = (np.cos(theta)) / np.sqrt(wp[0])
        ty2 = (np.sin(theta)) / np.sqrt(wp[1])

        ty1_eps = (np.cos(theta)) / np.sqrt(wp_eps[0])
        ty2_eps = (np.sin(theta)) / np.sqrt(wp_eps[1])

        ty = np.stack((ty1, ty2))
        tQ = inv(vp.transpose())
        # tQ = vp.transpose()
        tx = np.matmul(tQ, ty)

        ty_eps = np.stack((ty1_eps, ty2_eps))
        tQ_eps = inv(vp_eps.transpose())
        tx_eps = np.matmul(tQ_eps, ty_eps)

        tx1 = np.array(tx[0]).flatten()
        tx2 = np.array(tx[1]).flatten()

        tx_eps1 = np.array(tx_eps[0]).flatten()
        tx_eps2 = np.array(tx_eps[1]).flatten()

        # Safety envelope
        plt.plot(tx1, tx2, linewidth=3, color='grey')
        # plt.plot(0, 0, 'k*', markersize=4, mew=0.6)  # global equilibrium (star)
        # plt.plot(0, 0, 'ko-', markersize=7, mew=1, markerfacecolor='none')  # global equilibrium (circle)

        # HAC switch envelope
        # if self.simplex_enable:
        #     plt.plot(tx_eps1, tx_eps2, 'k--', linewidth=0.8, label=r"$\partial\Omega_{HAC}$")

        # HPC switch envelope
        # plt.plot(tx_hpc1, tx_hpc2, 'b--', linewidth=0.8, label=r"$\partial\Omega_{HPC}$")


if __name__ == '__main__':
    pass
