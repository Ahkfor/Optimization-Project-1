import pandas as pd
import gurobipy as gp
import numpy as np
from gurobipy import GRB


income_df = pd.read_csv('new_income.csv')
employment_df = pd.read_csv('new_employment.csv')
population_df = pd.read_csv('new_population.csv')
facility_df = pd.read_csv('new_child_care.csv')
location_df = pd.read_csv('new_potential_loc.csv')

merged_df = pd.merge(income_df, employment_df, on = 'zip_code')

def classify_demand(row):
    if row['employment rate'] >= 0.6 or row['average income'] <= 60000:
        return 1
    else:
        return 0

merged_df['High-Demand'] = merged_df.apply(classify_demand, axis=1)

merged_df = pd.merge(merged_df, population_df, on = 'zip_code')

merged_df['p_0-5'] = merged_df['-5']
merged_df['p_5-12'] = np.ceil(merged_df['5-9'] + 3/5 * merged_df['10-14'])
merged_df['p_0-12'] = merged_df['p_0-5'] + merged_df['p_5-12']

df = merged_df[['zip_code', 'High-Demand', 'p_0-5', 'p_5-12', 'p_0-12']]
facility_df['c_0-5'] = facility_df['infant_capacity'] + facility_df['toddler_capacity'] + facility_df['preschool_capacity'] + np.floor(5/12 * facility_df['children_capacity'])
facility_df['c_5-12'] = np.floor(7/12 * facility_df['children_capacity'])
facility_df['c_0-12'] = facility_df['c_0-5'] + facility_df['c_5-12']

facility_df = facility_df[['zip_code' ,'facility_id', 'c_0-5', 'c_5-12', 'c_0-12', 'latitude', 'longitude']]


# Problem 1
# Since each area is independent of each other, model each district differently
total_cost = 0
for index, row in df.iterrows():
    zip_code = row['zip_code']
    facilities = facility_df[facility_df['zip_code'] == zip_code].reset_index().copy()

    # Outstanding need for 0-12 children
    total_need = np.floor(row['p_0-12']*(1/3+row['High-Demand']*1/6)) - facilities['c_0-12'].sum()

    # Outstanding need for 0-5 children
    infant_need = np.floor(row['p_0-5']*2/3) - facilities['c_0-5'].sum()

    # Set up gurobi model
    model = gp.Model()
    # Suppress output
    model.setParam('OutputFlag', 0)
    x = model.addVars(3, vtype=GRB.INTEGER, lb=0)
    y = model.addMVar((2, len(facilities)), vtype=GRB.INTEGER, lb=0)
    costs = [65000, 95000, 115000]
    capacity = [100, 200, 400]
    infant_capacity = [50, 100, 200]
    obj = gp.quicksum(costs[i] * x[i] for i in range(3))
    total_expand = gp.quicksum(x[i]*capacity[i] for i in range(3))
    infant_expand = gp.quicksum(x[i]*infant_capacity[i] for i in range(3))

    # Iterate over each facility
    for idx, facility in facilities.iterrows():
        current_capacity = facility['c_0-12']
        max_expansion = min(0.2*current_capacity, 500)
        if current_capacity == 0:
            continue
        base_cost = 20000 + 200*current_capacity
        obj += base_cost*(y[0, idx]/current_capacity) + 100*y[1, idx]
        model.addConstr(y[1, idx] <= y[0, idx])
        model.addConstr(y[0, idx] <= max_expansion)
        total_expand += y[0, idx]
        infant_expand += y[1, idx]

    model.addConstr(total_expand >= total_need)
    model.addConstr(infant_expand >= infant_need)
    model.setObjective(obj, GRB.MINIMIZE)
    model.optimize()
    obj_val = model.getAttr('ObjVal')
    print(obj_val)
    total_cost += obj_val
print(total_cost)


