# Peer-to-Peer Electricity Market
Project contributors: Ryan Hekman, Kelsey Sweeney, and Ben Glass

## Context
Implementation of a P2P Electricity Market on a distribution system with battery storage. Theory, problem formulation, and algorithms are based on the work from [Ullah & Park](https://ieeexplore.ieee.org/document/9369412) (2021)

## Problem Setup*
- **Nodes:** 4 (including Slack bus)
- **Network Model Type:** Radial (Linearized DistFlow)
- **Timesteps:** 4
- **Timestep Duration:** 4 hours
- **Optimization Solver:** SciPy [Optimize](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.minimize.html).

* A detailed table of values used for all voltage, power, and DER constraints can be accessed on request.
- 

## Notes
This project was completed for as a final project for EC500 at Boston University (Spring 2025). Pull requests and comments are welcome.



