# Peer-to-Peer Electricity Market
Project contributors: Ryan Hekman, Kelsey Sweeney, and Ben Glass

## Context
Implementation of a P2P Electricity Market on a distribution system with battery storage. Theory, problem formulation, and algorithms are based on the work from [Ullah & Park](https://ieeexplore.ieee.org/document/9369412) (2021).

## Problem Setup
- **Nodes:** 4 (including Slack bus)
- **Network Model Type:** Radial (Linearized DistFlow)
- **Timesteps:** 4
- **Timestep Duration:** 4 hours
- **Optimization Solver:** SciPy [Optimize](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.minimize.html).
  
**Note:** A detailed table of values used for all line characteristics, voltage, power, and DER constraints can be accessed on request.

## File Structure
- **code.py** : Is a standalone script that optimizes power injection of four nodes over four timesteps.
- **ConstraintTesting.py** : Runs problem with varying constraint values to test constraint sensetivity. 
- **energy_trade_function.py** : A script that refactors much of code.py into a function, most min/max parameters are hard-coded, whereas schedulable injections and injection targets are arguments. Returns all optimal trades for all times. Is called by time_horizons.py
- **time_horizons.py** : includes energy_trade_function, calls the solver iteratively, walking through a block of schedulable parameters. Every iteration, it recalculates and updates initial battery states for the next round.
	To run time_horizons.py:
		input the desired scheduled injections, utility targets, utility priority (how much the utility cares about meeting the target for that indexed time), and initial battery states for time zero.
		Make sure row number for scheduled injections matches number of entries for utility targets and priorities.
	Initial battery state should always be 3 entries (system has 3 batteries)
- **simulationNodeZeroReq.py** : A copy of code.py modified to simulate and graph how the battery at node 1 will change energy state in respond to varying requests from node 0.

## More Info
This project was completed as a final project for EC500 (Control of Sustainable Power Systems) at Boston University during Spring 2025.
