# import matplotlib
# matplotlib.use('agg')

import matplotlib.pyplot as plt
import scipy.integrate as integrate
import sympy as sp

from modules.corrections import eps_at_isco
from modules.isco_values import *
from modules.kerr_functions import *


class OriThorneExpansion:

    def _transition_start(self, t, y):
        return y[0] - 1.01*self._r_isco

    def _transitions(self, t, y):
        return y[0] - self._r_isco

    def _transition_end(self, t, y):
        return y[0] - 0.99*self._r_isco
    _transition_end.terminal = True

    def _ders(self, t, y):
        r, rdot = y
        return [rdot, -self._alpha*(r-self._r_isco) ** 2 - self._eta*self._beta*self._kappa*t]

    def _evolve(self):
        sol = None
        done = False
        count = 1
        while not done:
            print('starting OT inspiral, number', count, 'of the same inspiral')
            # noinspection PyTypeChecker
            sol = integrate.solve_ivp(self._ders,
                                      (self._tau_init, self._span),
                                      (self._r_isco+(-self._eta*self._beta*self._kappa*self._tau_init/self._alpha)**0.5,
                                       -0.5*(-self._eta*self._beta*self._kappa/(self._alpha*self._tau_init))**0.5),
                                      dense_output=True,
                                      events=[self._transitions, self._transition_start, self._transition_end],
                                      method='Radau')
            if len(sol.t_events[2]) > 0:
                done = True
                self._transition_end = sol.t_events[2][0]
                self._transition_start = sol.t_events[1][0]
                self._transition_time = sol.t_events[0][0]
            else:
                self._span *= 1.2
                count += 1
        return sol.sol

    def evaluate_in(self, ts):
        self._taus = ts
        self._rs = self._ode_solution.__call__(ts)[0]

    def evaluate_in_transition(self):
        self._taus = np.linspace(self._transition_start, self._transition_end, 200, endpoint=True)
        self._rs = self._ode_solution.__call__(self._taus)[0]

    def __init__(self, eob_equivalent, a: float, eta: float,
                 span: float = 6000, tau_init: float = -1e7) -> None:
        self._taus = None
        self._rs = None
        self._eob_equivalent = eob_equivalent
        self._tau_init = tau_init
        self._span = span
        self._a = a
        self._eta = eta
        self._r_isco = risco(self._a)
        r, l_z, e = sp.symbols('r lz e')
        self._V = 1 - 2 / r + (l_z ** 2 + a ** 2 - e ** 2 * a ** 2) / r ** 2 - 2 * (l_z - a * e) ** 2 / r ** 3
        self._alpha = 0.25 * self._V.diff(r, 3).subs([(r, self._r_isco), (e, e_isco(self._a)), (l_z, lz_isco(self._a))])
        self._beta = -0.5 * (self._V.diff(r, l_z).subs([(r, self._r_isco), (e, e_isco(self._a)), (l_z, lz_isco(self._a))])
                             + omega_isco(self._a) * self._V.diff(r, e).subs(
                    [(r, self._r_isco), (e, e_isco(self._a)), (l_z, lz_isco(self._a))]))
        self._kappa = 32. / 5 * omega_isco(self._a) ** (7. / 3) * eps_at_isco(self._a) * (
                1 + self._a / self._r_isco ** 1.5) / np.sqrt(
            1 - 3 / self._r_isco + 2 * self._a / self._r_isco ** 1.5)
        self._r_break = (self._beta*self._kappa*self._eta)**0.4*self._alpha**(-0.6)
        self._ode_solution = self._evolve()

    def get_eob_equivalent(self):
        return self._eob_equivalent

    def get_r_break(self):
        return self._r_break

    def get_tau_init(self):
        return self._tau_init

    def get_isco_crossing_time(self):
        return self._transition_time

    def get_taus(self):
        return self._taus

    def get_rs(self):
        return self._rs

    def plot_radial_trajectory(self):
        plt.plot(self._taus, self._rs, '.', label='kesdens_expansion')
        plt.plot(self._taus, np.ones(len(self._taus)) * self._r_isco)

    def plot_shifted_radial_trajectory(self):
        plt.plot(self._taus - self.get_isco_crossing_time(), self._rs, 'r.', label='expansion')
        plt.plot(self._taus - self.get_isco_crossing_time(), np.ones(len(self._taus)) * self._r_isco)
        plt.ylim((self._r_isco * 0.95, self._r_isco * 1.05))


class OriThorneExpansionDimensionless:
    _tinit = -2.e6
    _tend = 3.412e0
    _solinit = [np.sqrt(-_tinit), -0.5 / np.sqrt(-_tinit)]
    _points = int(1e5)

    @staticmethod
    def _ders(t, y):
        x, xdot = y
        return [xdot, -x**2 - t]

    @staticmethod
    def _transitions(t, y):
        return y[0]

    def _evolve(self):
        sol = integrate.solve_ivp(self._ders,
                                  (OriThorneExpansionDimensionless._tinit, OriThorneExpansionDimensionless._tend),
                                  OriThorneExpansionDimensionless._solinit,
                                  dense_output=True, events=self._transitions, method='Radau')
        self._transition_time = sol.t_events[0][0]
        return sol.sol

    def __init__(self) -> None:
        self.a = 0
        self._ode_solution = self._evolve()
        self._ts = np.linspace(-4, 3.5, 1000)
        self._xs = self._ode_solution.__call__(self._ts)[0]

    def get_data(self):
        return self._ts, self._xs

    def plot_data(self):
        tsminus = np.linspace(-4, 0, 200)
        tsplus = np.linspace(1, 4, 200)
        plt.figure(figsize=(7, 4), dpi=200)
        plt.plot(tsminus, np.sqrt(-tsminus), 'k--')
        plt.plot(tsplus, -6/(tsplus-3.412)**2, 'k--')
        plt.plot(self._ts, self._xs, 'k')
        plt.ylim(-4, 3)
        plt.xlim(-4, 4)
        plt.hlines(0, -4, 4, linestyles='dotted')
        plt.vlines(0, -4, 4, linestyles='dotted')
        plt.gcf().gca().annotate(r'plunge at $T=3.412$',
                                 (3.412, -4), xytext=(2.06, -2), arrowprops={'arrowstyle': '->'})
        plt.xlabel(r'$T$')
        plt.ylabel(r'$X$')
        plt.tight_layout(pad=0.25)

    def get_isco_crossing_time(self):
        return self._transition_time
