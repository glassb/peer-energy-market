#test
import numpy as np
from scipy import linalg as linearalgebra
from energy_trade_function import solve

#how much the utility wants to receive (net) from the prosumers
utilitytarget = np.array([-20, -20, 10, -5, 10, -5])
utilitypriority = np.array([10, 0, 2, 0, 5, 0])

prosumerschedule = np.array([[-2.8, -5, -5],
                             [0.8, 3.4, 3.4],
                             [18, 12, 12],
                             [16.9, 8, 8],
                             [-1, 2, 2],
                             [-3, -3, -3]])


initialbatterystate = np.array([6, 12, 11])


for iteration in range(len(prosumerschedule) - 3):
  results = solve(prosumerschedule[iteration:iteration+4], initialbatterystate, utilitypriority[iteration:iteration+4], utilitytarget[iteration:iteration+4])



  # round all values to a specific decimal precision
  decimal_precision = 2
  for i in range(64):
    # Values that will display as -0.0 are rounded to zero
    if results[i] <= 0 and results[i] >= -1 * (0.1 ** (decimal_precision)):
      results[i] = 0
    results[i] = round(results[i], decimal_precision)

  # printing the output
  #for i in range(64):
  #  print(timesteps[i // 16], '--', decision_variables[i % 16], ':  ', results.x[i], 'per unit')

  # unsure what this is, but had to move it down below the solver
  transform = [[0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0],
               [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0],
               [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1]]

  fourTransform = linearalgebra.block_diag(transform, transform, transform, transform)



  # ----------------------------------------------------- Recovering P_injected_battery = Sum_P_ij - P_scheduled_inj

  # This block of code sums all trades from a particular node to all other nodes at timestep t into an array structure like below.
  # ts = 0, from node 0 | ts = 1, from node 1 | ts = 1, from node 2 | ts = 1, from node 3 |
  # ts = 1, from node 0 | ts = 2, from node 1 | ts = 2, from node 2 | ts = 2, from node 3 |
  # ts = 2, from node 0 | ts = 3, from node 1 | ts = 3, from node 2 | ts = 3, from node 3 |
  # ts = 3, from node 0 | ts = 4, from node 1 | ts = 4, from node 2 | ts = 4, from node 3 |

  idx = 0

  # excludes any injection at the slack! This only looks at the sum of the powers at bus 1, 2, and 3
  energyadded = np.zeros((12, 12))
  for i in range(4):
    for j in range(3):
      for k in range(3):
        if k < i:
          energyadded[i * 3 + j][k * 3 + j] = 1

  # produces a 12x64, that takes Pijt, and returns Pit (summing over j)
  # excludes any row that sums power injected at the slack, we do not want to include P0 injection in any of the battery constraints. It is unscheduled
  sumj_Pijt = np.zeros((12, 64))
  for i in range(4):
    for j in range(3):
      for k in range(4):
        sumj_Pijt[i * 3 + j][16 * i + 4 * j + k + 4] = 1


  # ------------------------------------ RYAN BATTERY STATE --------------------------------------------
  tradesum_arr = linearalgebra.block_diag(np.ones(4), np.ones(4), np.ones(4), np.ones(4))
  tradesum_arr_t = linearalgebra.block_diag(tradesum_arr, tradesum_arr, tradesum_arr, tradesum_arr)

  # Trade Sum
  tradesum = np.matmul(tradesum_arr_t, results)

  # power battery injects to node
  battery_power = np.matmul(sumj_Pijt, results) - np.ndarray.flatten(prosumerschedule[iteration:iteration+4])

  # battery state at the START of each timestep
  battery_state = np.ndarray.flatten(np.vstack((initialbatterystate, initialbatterystate, initialbatterystate, initialbatterystate))) - (np.matmul(energyadded, np.matmul(sumj_Pijt, results) - np.ndarray.flatten(prosumerschedule[iteration:iteration+4])) * 4)



  print("Battery State BEFORE timestep: \n", np.reshape(battery_state, (4, 3)))
  print("Battery Power:                 \n", np.reshape(battery_power, (4, 3)))
  print("Power Injected at all nodes:   \n", np.reshape(tradesum, (4, 4)))


  #resets the initial battery state for the next loop
  initialbatterystate = np.ndarray.flatten(battery_state[3:6])