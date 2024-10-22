import pandas as pd
import gurobipy as gp
from helper import *


# Identify high and normal demand areas
income_df = pd.read_csv('./data/avg_individual_income.csv')
employment_df = pd.read_csv('./data/employment_rate.csv')
employment_df = employment_df.rename(columns={'zipcode': 'ZIP code'})
income_employment_df = pd.merge(income_df, employment_df, on='ZIP code', how='outer')

high_demand_li = []
for index, row in income_employment_df.iterrows():
    income = row['average income']
    employment = row['employment rate']
    high_demand = 0
    if income:
        if income <= 60000:
            high_demand = 1
    if employment:
        if employment >= 0.6:
            high_demand = 1
    high_demand_li.append(high_demand)
income_df['high_demand'] = high_demand_li


# Location Problem
loc_df = pd.read_csv('./data/potential_locations.csv')
group_name = loc_df['zipcode'].unique()
max_facility_dict = {}

for zip_code in group_name:
    df = loc_df[loc_df['zipcode'] == zip_code].reset_index()
    model = gp.Model()
    model.setParam('OutputFlag', 0)
    x = model.addVars(len(df), vtype=gp.GRB.BINARY)
    model.setObjective(x.sum(), gp.GRB.MAXIMIZE)
    for i in range(len(df)-1):
        for j in range(i+1, len(df)):
            loc1 = (df['latitude'][i], df['longitude'][i])
            loc2 = (df['latitude'][j], df['longitude'][j])
            distance = calculate_distance(loc1, loc2)
            if distance < 0.06:
                model.addConstr(x[i] + x[j] <= 1)
    model.optimize()
    opt_val = model.getAttr('ObjVal')
    max_facility_dict[zip_code] = opt_val
print(max_facility_dict)