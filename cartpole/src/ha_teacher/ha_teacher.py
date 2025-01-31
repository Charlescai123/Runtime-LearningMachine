import os
import time
import copy
import numpy as np
import matplotlib.pyplot as plt
from numpy.linalg import inv
from numpy import linalg as LA

from src.physical_design import MATRIX_P, F, F_Simplex
from src.ha_teacher.mat_engine import MatEngine
from src.hp_student.agents.ddpg import DDPGAgent
from src.logger.logger import Logger, plot_trajectory
from src.utils.utils import energy_value, get_discrete_Ad_Bd, logger, ActionMode

np.set_printoptions(suppress=True)


class HATeacher:
    def __init__(self, teacher_cfg, cartpole_cfg):

        # Matlab Engine
        self.mat_engine = MatEngine(cfg=teacher_cfg.matlab_engine)

        # Teacher Configuration
        self.chi = teacher_cfg.chi
        self.epsilon = teacher_cfg.epsilon
        self.max_dwell_steps = teacher_cfg.tau

        self.teacher_enable = teacher_cfg.teacher_enable
        self.teacher_correct = teacher_cfg.teacher_correct

        # Cart-Pole Configuration
        self.mc = cartpole_cfg.mass_cart
        self.mp = cartpole_cfg.mass_pole
        self.g = cartpole_cfg.gravity
        self.l = cartpole_cfg.length_pole / 2
        self.freq = cartpole_cfg.frequency

        # Real-time status
        self._plant_state = None
        self._teacher_activate = False
        self._patch_center = np.array([0., 0., 0., 0.])
        self._patch_gain = F_Simplex  # F_simplex
        self._dwell_step = 0  # Dwell step
        self._activation_cnt = 0

    def reset(self, state):
        self._plant_state = state
        self._teacher_activate = False
        self._patch_center = np.array([0., 0., 0., 0.])
        self._patch_gain = F_Simplex  # F_simplex
        self._dwell_step = 0
        self._activation_cnt = 0  # Count of teacher activate times

    def update(self, state: np.ndarray):
        """
        Update real-time plant state and corresponding patch center if state is unsafe
        """

        self._plant_state = state
        energy = energy_value(state=state, p_mat=MATRIX_P)

        # When HA-Teacher activated
        if self._teacher_activate:

            # Deactivate it after dwell time
            if self._dwell_step >= self.max_dwell_steps:
                logger.debug(f"Reaching maximum dwell steps, deactivate HA-Teacher")
                self._teacher_activate = False

        # When HA-Teacher deactivated
        else:
            # Outside envelope boundary
            if energy >= self.epsilon:
                self._dwell_step = 0
                self._teacher_activate = True  # Activate teacher
                self._activation_cnt += 1  # Activation count plus 1
                self._patch_center = self._plant_state * self.chi  # Update patch center
                logger.debug(f"Activate HA-Teacher and updated patch center is: {self._patch_center}")

    def get_action(self):
        """
        Get updated teacher action during real-time
        """

        # If teacher is disabled or deactivated
        if self.teacher_enable is False or self._teacher_activate is False:
            return None, False

        As, Bs = self.get_As_Bs_by_state(state=self._plant_state)
        Ak, Bk = get_discrete_Ad_Bd(Ac=As, Bc=Bs, T=1 / self.freq)

        # Call Matlab Engine for patch gain (F_hat)
        F_hat, t_min = self.mat_engine.system_patch(Ak=Ak, Bk=Bk, chi=self.chi)

        if t_min > 0:
            print(f"LMI has no solution, use last updated patch")
        else:
            self._patch_gain = np.asarray(F_hat).squeeze()

        # State error form
        error_state = self._plant_state - self._patch_center

        # redundancy_term = self._patch_center - Ak @ self._patch_center
        # v1 = np.squeeze(redundancy_term[1] / Bk[1])
        # v2 = np.squeeze(redundancy_term[3] / Bk[3])
        # v = np.linalg.pinv(self.Bk).squeeze() @ (np.eye(4) - self.Ak) @ sbar_star
        # v = (v1 + v2) / 2

        # Action from HA-Teacher
        teacher_action = self._patch_gain @ error_state

        logger.debug(f"patch gain: {self._patch_gain}")
        logger.debug(f"self._plant_state: {self._plant_state}")
        logger.debug(f"self._patch_center: {self._patch_center}")
        logger.debug(f"Generated teacher action: {teacher_action}")

        assert self._dwell_step <= self.max_dwell_steps

        # Increment one dwell step
        self._dwell_step += 1
        logger.debug(f"HA-Teacher runs for dwell time: {self._dwell_step}/{self.max_dwell_steps}")

        return teacher_action, True

    def get_As_Bs_by_state(self, state: np.ndarray):
        """
        Update the physical knowledge matrices A(s) and B(s) in real-time based on the current state
        """
        x = state[0]
        x_dot = state[1]
        theta = state[2]
        theta_dot = state[3]

        As = np.zeros((4, 4))
        As[0][1] = 1
        As[2][3] = 1

        mc = self.mc
        mp = self.mp
        g = self.g
        l = self.l

        term = 4 / 3 * (mc + mp) - mp * np.cos(theta) * np.cos(theta)

        As[1][2] = -mp * g * np.sin(theta) * np.cos(theta) / (theta * term)
        As[1][3] = 4 / 3 * mp * l * np.sin(theta) * theta_dot / term
        As[3][2] = g * np.sin(theta) * (mc + mp) / (l * theta * term)
        As[3][3] = -mp * np.sin(theta) * np.cos(theta) * theta_dot / term

        Bs = np.zeros((4, 1))
        Bs[1] = 4 / 3 / term
        Bs[3] = -np.cos(theta) / (l * term)

        return As, Bs

    @property
    def plant_state(self):
        return self._plant_state

    @property
    def patch_center(self):
        return self._patch_center

    @property
    def patch_gain(self):
        return self._patch_gain

    @property
    def dwell_step(self):
        return self._dwell_step

    @property
    def activation_cnt(self):
        return self._activation_cnt
