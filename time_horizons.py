import numpy as np
from energy_trade_function import solve

utilitytarget = np.array([-20, -20, 10, -5, 10])
utilitypriority = np.array([10, 0, 2, 0, 5])

prosumerschedule = np.array([[-2.8, -5, -5],
                             [0.8, 3.4, 3.4],
                             [18, 12, 12],
                             [16.9, 8, 8],
                             [-1, 2, 2]])

#-3

initialbatterystate = np.array([6, 12, 11])


for i in range(len(prosumerschedule) - 3):
  initialbatterystate = solve(prosumerschedule[i:i+4], initialbatterystate, utilitypriority[i:i+4], utilitytarget[i:i+4])
  print(initialbatterystate)