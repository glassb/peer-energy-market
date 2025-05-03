# Peer-to-Peer Electricity Market
Implementation of a P2P Market on an 4-participant distribution system. 

Theory, optimization formulation, and algorithms are based on the work from Ullah & Park (2021): https://ieeexplore.ieee.org/document/9369412

This project was completed for as a final project for EC500 at Boston University (Spring 2025).
Project contributors: Ryan Hekman, Kelsey Sweeney, and Ben Glass

Scripts:
	code.py is a standalone script that optimizes power injection of four nodes over four timesteps
	energy_trade_function.py is a script that refactors much of code.py into a function, most min/max parameters are hard-coded, whereas schedulable injections and injection targets are arguments. Returns all optimal trades for all times.
	time_horizons.py includes energy_trade_function, calls the solver iteratively, walking through a block of schedulable parameters. Every iteration, it recalculates and updates initial battery states for the next round.

To run time_horizons.py:
	input the desired scheduled injections, utility targets, utility priority (how much the utility cares about meeting the target for that indexed time), and initial battery states for time zero.
	Make sure row number for scheduled injections matches number of entries for utility targets and priorities.
	Initial battery state should always be 3 entries (system has 3 batteries)