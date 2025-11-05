#!/usr/bin/env python3
"""
Example Mixed Integer Programming (MIP) problem using Gurobi

This solves a simple facility location problem:
- We have potential facility locations with opening costs
- We have customers with demands
- We need to decide which facilities to open and how to assign customers
- Goal: Minimize total cost (facility opening + transportation)

This is a good test problem that can scale to be computationally intensive.
"""

import gurobipy as gp
from gurobipy import GRB
import time
import sys

def solve_facility_location(num_facilities=20, num_customers=50, time_limit=3600):
    """
    Solve a facility location problem

    Args:
        num_facilities: Number of potential facility locations
        num_customers: Number of customers to serve
        time_limit: Time limit in seconds (default 1 hour)

    Returns:
        Dictionary with solution details
    """

    print(f"Setting up MIP problem with {num_facilities} facilities and {num_customers} customers...")
    start_time = time.time()

    # Create model
    model = gp.Model("facility_location")

    # Generate problem data
    import random
    random.seed(42)  # For reproducibility

    # Facility opening costs (random between 1000 and 5000)
    opening_costs = [random.randint(1000, 5000) for _ in range(num_facilities)]

    # Customer demands (random between 1 and 100)
    demands = [random.randint(1, 100) for _ in range(num_customers)]

    # Transportation costs (random between 10 and 500)
    transport_costs = [[random.randint(10, 500) for _ in range(num_facilities)]
                       for _ in range(num_customers)]

    # Facility capacities (random between 300 and 1000)
    capacities = [random.randint(300, 1000) for _ in range(num_facilities)]

    print(f"Problem setup complete. Starting optimization...")

    # Decision variables
    # x[i,j] = 1 if customer i is assigned to facility j
    x = model.addVars(num_customers, num_facilities, vtype=GRB.BINARY, name="assign")

    # y[j] = 1 if facility j is opened
    y = model.addVars(num_facilities, vtype=GRB.BINARY, name="open")

    # Objective: Minimize total cost
    model.setObjective(
        gp.quicksum(opening_costs[j] * y[j] for j in range(num_facilities)) +
        gp.quicksum(transport_costs[i][j] * demands[i] * x[i,j]
                   for i in range(num_customers)
                   for j in range(num_facilities)),
        GRB.MINIMIZE
    )

    # Constraints
    # 1. Each customer must be assigned to exactly one facility
    for i in range(num_customers):
        model.addConstr(
            gp.quicksum(x[i,j] for j in range(num_facilities)) == 1,
            name=f"customer_{i}"
        )

    # 2. Customers can only be assigned to open facilities
    for i in range(num_customers):
        for j in range(num_facilities):
            model.addConstr(
                x[i,j] <= y[j],
                name=f"open_{i}_{j}"
            )

    # 3. Facility capacity constraints
    for j in range(num_facilities):
        model.addConstr(
            gp.quicksum(demands[i] * x[i,j] for i in range(num_customers)) <= capacities[j],
            name=f"capacity_{j}"
        )

    # Set time limit
    model.Params.TimeLimit = time_limit

    # Set number of threads (0 = use all available)
    model.Params.Threads = 0

    # Enable output
    model.Params.OutputFlag = 1

    print("\n" + "="*70)
    print("Starting Gurobi Optimizer")
    print("="*70)

    # Optimize
    model.optimize()

    solve_time = time.time() - start_time

    # Collect results
    result = {
        'status': model.Status,
        'solve_time': solve_time,
        'num_facilities': num_facilities,
        'num_customers': num_customers
    }

    if model.Status == GRB.OPTIMAL:
        result['optimal'] = True
        result['objective_value'] = model.ObjVal
        result['gap'] = 0.0

        # Count opened facilities
        opened = [j for j in range(num_facilities) if y[j].X > 0.5]
        result['facilities_opened'] = len(opened)
        result['opened_facility_ids'] = opened

        print("\n" + "="*70)
        print("OPTIMAL SOLUTION FOUND!")
        print("="*70)
        print(f"Objective value: ${result['objective_value']:,.2f}")
        print(f"Facilities opened: {result['facilities_opened']} out of {num_facilities}")
        print(f"Solve time: {solve_time:.2f} seconds")

    elif model.Status == GRB.TIME_LIMIT:
        result['optimal'] = False
        result['objective_value'] = model.ObjVal if model.SolCount > 0 else None
        result['gap'] = model.MIPGap if model.SolCount > 0 else None

        print("\n" + "="*70)
        print("TIME LIMIT REACHED")
        print("="*70)
        if model.SolCount > 0:
            print(f"Best solution found: ${result['objective_value']:,.2f}")
            print(f"MIP gap: {result['gap']*100:.2f}%")
        else:
            print("No feasible solution found within time limit")
        print(f"Solve time: {solve_time:.2f} seconds")

    else:
        result['optimal'] = False
        print("\n" + "="*70)
        print(f"Optimization ended with status: {model.Status}")
        print("="*70)

    return result


def main():
    """Main entry point"""

    print("="*70)
    print("Gurobi MIP Example: Facility Location Problem")
    print("="*70)
    print()

    # Check Gurobi license
    try:
        env = gp.Env()
        env.dispose()
        print("✓ Gurobi license verified")
    except Exception as e:
        print(f"✗ Gurobi license error: {e}")
        print("\nMake sure you have a valid Gurobi license.")
        print("For students: Get a free WLS Academic license at https://www.gurobi.com/academia/")
        sys.exit(1)

    print()

    # You can adjust problem size here
    # Larger problems = more computation time = better test of VM performance
    result = solve_facility_location(
        num_facilities=20,
        num_customers=50,
        time_limit=3600  # 1 hour max
    )

    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"Problem size: {result['num_facilities']} facilities, {result['num_customers']} customers")
    print(f"Status: {'Optimal' if result['optimal'] else 'Non-optimal'}")
    if result['objective_value']:
        print(f"Objective: ${result['objective_value']:,.2f}")
    print(f"Total time: {result['solve_time']:.2f} seconds")
    print("="*70)

    return result


if __name__ == "__main__":
    main()
