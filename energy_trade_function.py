def solve(inj, battlvl, subtarget, subweight):

  import numpy as np
  from scipy import optimize as opt
  from scipy import linalg as linearalgebra

  # Problem setup
  timeblocks_no = 4
  vars_per_timeblock = 16
  nodecount = 4
  timestep_duration = 4  # duration in hours

  # divide voltages by V_b
  v_base = 10000  # V
  # divide powers by S_b
  s_base = 1000  # W
  # divide impedances by Z_b
  z_base = (v_base * v_base) / s_base  # kOhms

  # injection schedule for node i at time t (i=1 t=0, i=2 t=0, i=3 t=0, i=1 t=1, i=2 t=1.....), a negative injection is load, positive is generation
  # Slack bus NOT included!!!
  # t1 = 0000 - 0400, t2 = 0400 - 0800, t3 = 0800 - 1200, t4 = 1200 - 1600
  # node 1,2,3 have PV.

  scheduledinjection = inj.reshape(12, 1)
  hardware_p_min = [-38.4, -38.4, -38.4, -38.4, -38.4, -38.4, -38.4, -38.4, -38.4, -38.4, -38.4, -38.4]
  hardware_p_max = [38.4, 38.4, 38.4, 38.4, 38.4, 38.4, 38.4, 38.4, 38.4, 38.4, 38.4, 38.4]

  F_r = np.diag([1.3509 / z_base, 1.17024 / z_base, 0.84111 / z_base])
  F_x = np.diag([1.32349 / z_base, 1.14464 / z_base, 0.82271 / z_base])

  q_constant = np.array([[2],
                         [2],
                         [2]])

  # upper/lower bounds in p.u.
  fmax = np.multiply(100, [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1])
  fmin = np.multiply(100, [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1])

  # Start each battery with 50kWh, all have the same hardware settings
  # Slack has no battery constraints, and no battery! These are indexed beginning at node 1
  batt_initial = battlvl.reshape(3, 1)
  batt_min_e = np.array([[2], [10], [4]])  # user set minimum charge state
  batt_max_e = np.array([[12], [12], [22]])  # user set maximum charge state (powerwall is 13.5, user 3 has two powerwall batteries)
  batt_min_p = np.array([[-7.5], [-7.5], [-7.5]])  # 40A breaker 240V, at 80% capacity
  batt_max_p = np.array([[7.5], [7.5], [7.5]])

  # weights for cost function
  #refactor
  timepoint_weights = subweight.reshape(4,1)

  # for cost function
  #refactor
  P_0_target = subtarget.reshape(4,1)

  # --------------------------------------------------------
  '''
  Decision Variables Index: [24 energy trades]
  [00 01 02 03 10 11 12 13 20 21 22 23 30 31 32 33]
  
  00 01 02 03
  10 11 12 13
  20 21 22 23
  30 31 32 33
  '''
  # labels for printing output
  decision_variables = ['00', '01', '02', '03', '10', '11', '12', '13', '20', '21', '22', '23', '30', '31', '32', '33']
  timesteps = ['T1', 'T2', 'T3', 'T4']

  # we can set individual bounds for any of the decision variables
  bounds = []
  # ---------------------------------- General Variables


  # ---------------------------------- b part 1: HARDWARE POWER CONSTRAINTS
  # x is a vector of 16*4 variables
  # Incidence matrix so that sum_pij * x(optimization variables) = P_b + P_i
  sum_pij = np.array([[0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0],
                      [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0],
                      [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1]])

  sum_pij_4_timesteps = linearalgebra.block_diag(sum_pij, sum_pij, sum_pij, sum_pij)

  # might need to play around with these values
  # hardware_p_min = [-38.4, -38.4, -38.4, -38.4, -38.4, -38.4, -38.4, -38.4, -38.4, -38.4, -38.4, -38.4]
  # hardware_p_max = [38.4, 38.4, 38.4, 38.4, 38.4, 38.4, 38.4, 38.4, 38.4, 38.4, 38.4, 38.4]

  # all the input arrays must have same number of dimensions, but the array at index 0 has 1 dimension(s) and the array at index 1 has 2 dimension(s)

  constraint_19bp1_min = {'type': 'ineq', 'fun': lambda x: np.matmul(sum_pij_4_timesteps, x) - hardware_p_min}
  constraint_19bp1_max = {'type': 'ineq', 'fun': lambda x: hardware_p_max - np.matmul(sum_pij_4_timesteps, x)}

  # -----------------------------------b part 2: POWER TRADING CONSTRAINTS

  # this is the forcasted amount that we anticipate the node will demand for t=1,2,3,4
  P_nd = np.array([[1],  # t=1 node 1
                   [1],  # t=1 node 2
                   [1],
                   [1],  # t=2
                   [1],
                   [1],
                   [1],  # t=3
                   [1],
                   [1],
                   [1],  # t=4
                   [1],
                   [1]])

  # sum_pij_4_timesteps = linearalgebra.block_diag(sum_pij,sum_pij,sum_pij,sum_pij)

  # this is the forcasted amount that we anticipate the PV panel will be able to produce for t=1,2,3,4
  P_a_Pv = np.array([[6],  # t=1 node 1
                     [6],  # t=1 node 2
                     [6],
                     [6],  # t=2
                     [6],
                     [6],
                     [6],  # t=3
                     [6],
                     [6],
                     [6],  # t=4
                     [6],
                     [6]])

  P_i_min = -1 * P_nd

  P_i_max = P_a_Pv - P_nd

  constraint_19bp2_min = {'type': 'ineq',
                          'fun': lambda x: np.matmul(sum_pij_4_timesteps, x) - np.ndarray.flatten(P_i_min)}
  constraint_19bp2_max = {'type': 'ineq',
                          'fun': lambda x: np.ndarray.flatten(P_i_max) - np.matmul(sum_pij_4_timesteps, x)}

  # ---------------------------------- c: VOLTAGE CONSTRAINTS

  # make R matrix and v bar
  big_Wbar = np.array([[1, -1, 0, 0],  # 0 -> 1
                       [0, 1, -1, 0],  # 1 -> 2
                       [0, 0, 1, -1]])  # 2 -> 3

  big_W = np.array([big_Wbar[0][1:],
                    big_Wbar[1][1:],
                    big_Wbar[2][1:]])

  little_wbar = np.array([[big_Wbar[0][0]],
                          [big_Wbar[1][0]],
                          [big_Wbar[2][0]]])

  big_W_inv = np.linalg.inv(big_W)

  big_W_inv_T = np.transpose(big_W_inv)

  # values adopted from paper 43 referenced in Ullah and Park. Units in ohms.
  # F_r = np.diag([1.3509/z_base, 1.17024/z_base, 0.84111/z_base])
  # F_x = np.diag([1.32349/z_base, 1.14464/z_base, 0.82271/z_base])

  # q_constant = np.array([[2],
  # [2],
  # [2]])

  # v^2 = (R_matrix * sum_pij * x) + v_bar
  R_matrix = np.matmul(np.matmul(big_W_inv, F_r), big_W_inv_T)  # 3x3
  v_bar = np.matmul(big_W_inv, -1 * little_wbar) + np.matmul(np.matmul(np.matmul(big_W_inv, F_x), big_W_inv_T),
                                                             q_constant)  # 3x1

  R_matrix_4_timesteps = linearalgebra.block_diag(R_matrix, R_matrix, R_matrix, R_matrix)  # 12x12
  v_bar_4_timesteps = np.vstack((v_bar, v_bar, v_bar, v_bar))  # 12x1

  # upper and lower bounds
  v_max_squared = 1.05 * 1.05
  v_min_squared = 0.95 * 0.95
  v_max = np.array([[v_max_squared], [v_max_squared], [v_max_squared], [v_max_squared], [v_max_squared], [v_max_squared],
                    [v_max_squared], [v_max_squared], [v_max_squared], [v_max_squared], [v_max_squared], [v_max_squared]])
  v_min = np.array([[v_min_squared], [v_min_squared], [v_min_squared], [v_min_squared], [v_min_squared], [v_min_squared],
                    [v_min_squared], [v_min_squared], [v_min_squared], [v_min_squared], [v_min_squared], [v_min_squared]])

  #                                                                    12x12                           12x64   64x1              12x1                12x1
  constraint_19c_min = {'type': 'ineq', 'fun': lambda x: np.matmul(R_matrix_4_timesteps, np.matmul(sum_pij_4_timesteps,
                                                                                                   x)) + np.ndarray.flatten(
    v_bar_4_timesteps - v_min)}
  constraint_19c_max = {'type': 'ineq', 'fun': lambda x: np.ndarray.flatten(v_max - v_bar_4_timesteps) - (
    np.matmul(R_matrix_4_timesteps, np.matmul(sum_pij_4_timesteps, x)))}

  # ---------------------------------- f: POWER FLOW CONSTRAINTS

  # Wbar matrix for 4 node system
  Wbar = [[1, -1, 0, 0],
          [0, 1, -1, 0],
          [0, 0, 1, -1]]

  # W matrix for 4 node system
  W = [Wbar[0][1:],
       Wbar[1][1:],
       Wbar[2][1:]]

  # linear transform to calculate f (convert energy trades to net nodal power injections at nodes 1->3)
  nodal_power_transform = [[0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0],
                           [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0],
                           [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1]]

  # block diagonalizing Wbar, W, and nodal_power_transform 4 times in order to account for 4 timesteps
  nodal_power_transform_4_timesteps = linearalgebra.block_diag(nodal_power_transform, nodal_power_transform,
                                                               nodal_power_transform, nodal_power_transform)
  W_inv_T = np.transpose(np.linalg.inv(W))
  W_inv_T_4_timesteps = linearalgebra.block_diag(W_inv_T, W_inv_T, W_inv_T, W_inv_T)

  # calculate A matrix for constraint: lb <= Ax <= ub
  f_matrix = np.matmul(W_inv_T_4_timesteps, nodal_power_transform_4_timesteps)

  # upper/lower bounds in p.u.
  # fmax = np.multiply(100,[1,1,1,1,1,1,1,1,1,1,1,1])
  # fmin = np.multiply(100,[-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1])

  # ----------------------------------------------------------------Battery Constraints

  # Incidence matrix so that sum_pij * x(optimization variables) = P_b + P_i
  sum_pij = np.array([[0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0],
                      [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0],
                      [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1]])

  sum_pij_4_timesteps = linearalgebra.block_diag(sum_pij, sum_pij, sum_pij, sum_pij)


  batt_initial_t = np.vstack((batt_initial, batt_initial, batt_initial, batt_initial))
  batt_min_e_t = np.vstack((batt_min_e, batt_min_e, batt_min_e, batt_min_e))
  batt_max_e_t = np.vstack((batt_max_e, batt_max_e, batt_max_e, batt_max_e))
  batt_min_p_t = np.vstack((batt_min_p, batt_min_p, batt_min_p, batt_min_p))
  batt_max_p_t = np.vstack((batt_max_p, batt_max_p, batt_max_p, batt_max_p))

  # produces a 12x64, that takes Pijt, and returns Pit (summing over j)
  # excludes any row that sums power injected at the slack, we do not want to include P0 injection in any of the battery constraints. It is unscheduled
  sumj_Pijt = np.zeros(((nodecount - 1) * timeblocks_no, vars_per_timeblock * timeblocks_no))
  for i in range(timeblocks_no):
    for j in range(nodecount - 1):
      for k in range(nodecount):
        sumj_Pijt[i * (nodecount - 1) + j][vars_per_timeblock * i + (nodecount) * j + k + nodecount] = 1

  # produces the matrix that sums all previous power injections into a battery (it is a 3x3 identity that appears in every submatrix below the diagonal in a 12x12)
  # when multiplying sumPijt(x) into this matrix, it produces the energy state at the start of time interval t for battery at node i
  '''
  example with a 2x2 in an 8x8
  0  0  0  0  0  0  0  0
  0  0  0  0  0  0  0  0
  1  0  0  0  0  0  0  0 
  0  1  0  0  0  0  0  0
  1  0  1  0  0  0  0  0
  0  1  0  1  0  0  0  0
  1  0  1  0  1  0  0  0
  0  1  0  1  0  1  0  0
  '''

  # excludes any injection at the slack! This only looks at the sum of the powers at bus 1, 2, and 3
  energyadded = np.zeros(((nodecount - 1) * timeblocks_no, (nodecount - 1) * timeblocks_no))
  for i in range(timeblocks_no):
    for j in range(nodecount - 1):
      for k in range(nodecount - 1):
        if k < i:
          energyadded[i * (nodecount - 1) + j][k * (nodecount - 1) + j] = 1

  # create a matrix that is a 3x12, which will sum the power injected to each battery.
  totalbattpower = np.identity((nodecount - 1))
  totalbattpower = np.hstack((totalbattpower, totalbattpower, totalbattpower, totalbattpower))


  # (19e) constraint matrix
  e_constraints_per_time = 10
  e_constraint_mtx = np.zeros((e_constraints_per_time * timeblocks_no, vars_per_timeblock * timeblocks_no))

  for i in range(timeblocks_no):  # this loop iterates through time blocks

    # Trade Balance, power sent = power received from i to j
    e_constraint_mtx[0 + (i * e_constraints_per_time)][1 + (i * vars_per_timeblock)] = 1;  # 0 -> 1
    e_constraint_mtx[0 + (i * e_constraints_per_time)][4 + (i * vars_per_timeblock)] = 1;  # 1 -> 0
    e_constraint_mtx[1 + (i * e_constraints_per_time)][2 + (i * vars_per_timeblock)] = 1;  # 0 -> 2
    e_constraint_mtx[1 + (i * e_constraints_per_time)][8 + (i * vars_per_timeblock)] = 1;  # 2 -> 0
    e_constraint_mtx[2 + (i * e_constraints_per_time)][3 + (i * vars_per_timeblock)] = 1;  # 0 -> 3
    e_constraint_mtx[2 + (i * e_constraints_per_time)][12 + (i * vars_per_timeblock)] = 1;  # 3 -> 0
    e_constraint_mtx[3 + (i * e_constraints_per_time)][6 + (i * vars_per_timeblock)] = 1;  # 1 -> 2
    e_constraint_mtx[3 + (i * e_constraints_per_time)][9 + (i * vars_per_timeblock)] = 1;  # 2 -> 1
    e_constraint_mtx[4 + (i * e_constraints_per_time)][7 + (i * vars_per_timeblock)] = 1;  # 1 -> 3
    e_constraint_mtx[4 + (i * e_constraints_per_time)][13 + (i * vars_per_timeblock)] = 1;  # 3 -> 1
    e_constraint_mtx[5 + (i * e_constraints_per_time)][11 + (i * vars_per_timeblock)] = 1;  # 2 -> 3
    e_constraint_mtx[5 + (i * e_constraints_per_time)][14 + (i * vars_per_timeblock)] = 1;  # 3 -> 2

    # Self-trades
    e_constraint_mtx[6 + (i * e_constraints_per_time)][0 + (i * vars_per_timeblock)] = 1;  # 0 -> 0
    e_constraint_mtx[7 + (i * e_constraints_per_time)][5 + (i * vars_per_timeblock)] = 1;  # 1 -> 1
    e_constraint_mtx[8 + (i * e_constraints_per_time)][10 + (i * vars_per_timeblock)] = 1;  # 2 -> 2
    e_constraint_mtx[9 + (i * e_constraints_per_time)][15 + (i * vars_per_timeblock)] = 1;  # 3 -> 3

  # ---------------------------------- CONSTRAINTS
  constraint = (
    # (19bp1) constraints: Harware Power Constraints
    constraint_19bp1_min,
    constraint_19bp1_max,


    # (19c) constraints: Voltage Constraints
    constraint_19c_min,
    constraint_19c_max,

    # (19d) constraints
    {'type': 'ineq', 'fun': lambda x: fmax - np.matmul(f_matrix, x)},
    {'type': 'ineq', 'fun': lambda x: np.multiply(-1, fmin) + np.matmul(f_matrix, x)},

    # (19e) constraints
    {'type': 'eq', 'fun': lambda x: np.matmul(e_constraint_mtx, x)},  # do all at once, timesteps now included

    # Battery Constraints
    # Power Min
    {'type': 'ineq', 'fun': lambda x: np.matmul(sumj_Pijt, x) - np.ndarray.flatten(scheduledinjection + batt_min_p_t)},
    # Power Max
    {'type': 'ineq', 'fun': lambda x: np.ndarray.flatten(scheduledinjection + batt_max_p_t) - np.matmul(sumj_Pijt, x)},
    # Charge State Min
    {'type': 'ineq', 'fun': lambda x: np.ndarray.flatten(batt_initial_t - batt_min_e_t) - (np.matmul(energyadded,np.matmul(sumj_Pijt,x) - np.ndarray.flatten(scheduledinjection)) * timestep_duration)},
    # Charge State Max
    {'type': 'ineq', 'fun': lambda x: np.ndarray.flatten(batt_max_e_t - batt_initial_t) + (np.matmul(energyadded,np.matmul(sumj_Pijt,x) - np.ndarray.flatten(scheduledinjection)) * timestep_duration)},
    # Final Charge State, return to where it started
    {'type': 'eq',
     'fun': lambda x: np.matmul(totalbattpower, (np.matmul(sumj_Pijt, x) - np.ndarray.flatten(scheduledinjection)))},
  )


  # set initial guess for every prosumer to get all their power from the grid
  initial_guess = np.tile(np.zeros(vars_per_timeblock), timeblocks_no)
  for i in range(timeblocks_no):
    for j in range(nodecount - 1):
      initial_guess[(j + 1) + (i * vars_per_timeblock)] = scheduledinjection[j + (i * (nodecount - 1))][0] * -1
      initial_guess[((j + 1) * nodecount) + (i * vars_per_timeblock)] = scheduledinjection[j + (i * (nodecount - 1))][0]



  # -------------------------------- COST FUNCTION --------------------------------------------
  def cost_function(x, P_0_target, timepoint_weights, resistance_matrix, vbar):
    # Kelsey's P0 Target Injection
    # setting up structure/variables for cost function
    sum_Pi0 = np.array([0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0])
    sum_Pi0t = linearalgebra.block_diag(sum_Pi0, sum_Pi0, sum_Pi0, sum_Pi0)

    sumPij = linearalgebra.block_diag(np.ones(4), np.ones(4), np.ones(4))
    sumPij = np.hstack((np.zeros((3, 4)), sumPij))
    sumPijt = linearalgebra.block_diag(sumPij, sumPij, sumPij, sumPij)

    weights_diag = np.diag(np.ndarray.flatten(timepoint_weights))

    # Kelsey's Grid Operator Power Targets
    P0_weighted_targetdiff = np.matmul(weights_diag, np.matmul(sum_Pi0t, x) - np.ndarray.flatten(P_0_target))
    P0_target_penalty = (np.matmul(np.transpose(P0_weighted_targetdiff), P0_weighted_targetdiff))


    # Ryan's middleman restriction
    # Sums all the outgoing (positive) trades. This is convex because max is convex. If there is a middleman trade, the outgoing trade from origin to destination is duplicated as a middleman outgoing
    # squared to make the function differentiable at every point, easier for the optimizer
    middleman_penalty = ((np.matmul(np.ones(64), np.maximum(np.zeros(64), x))) ** 2) * 0.01
    return middleman_penalty + P0_target_penalty

  # ---------------------------- END COST FUNCTION -------------------------------------------------------


  # set initial guess for every prosumer to get all their power from the grid
  initial_guess = np.tile(np.zeros(vars_per_timeblock), timeblocks_no)
  for i in range(timeblocks_no):
    for j in range(nodecount - 1):
      initial_guess[(j + 1) + (i * vars_per_timeblock)] = scheduledinjection[j + (i * (nodecount - 1))][0] * -1
      initial_guess[((j + 1) * nodecount) + (i * vars_per_timeblock)] = scheduledinjection[j + (i * (nodecount - 1))][0]



  # return results of optimization problem

  # Status:
  # 0 = optimal solution found
  # 1 = iteration limit reached
  # 2 = infeasible
  # 3 = unbounded
  # 6 = ill-conditioned matrix
  # 8 = did not converge in iteration limit
  # 9 = failed, can't make further progress
  results = opt.minimize(fun=cost_function, args=(P_0_target, timepoint_weights, R_matrix_4_timesteps, v_bar_4_timesteps),
                         x0=initial_guess, constraints=constraint,
                         options={"maxiter": 100, "ftol": 1e-5, "disp": True})  # can add method="method"


  return results.x