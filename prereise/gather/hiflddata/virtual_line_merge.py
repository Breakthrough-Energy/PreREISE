"""
Read data 
        --  branch.csv
Write data for grid simulation
        -- branch.csv
Core Tasks
        -- Merge the parallel virtual lines
Core Subtask   
        -- 1 For virtual lines ehich have the same ends, keep one of them and delete others
        -- 3 Calculate the new x and rateA of this line       
"""

import pandas as pd


def sort_tu(t1):
    if t1[0] > t1[1]:
        a = t1[0]
        b = t1[1]
        t1 = (b, a)
    return t1


def update_branch(branches, br_update, br_delete):
    for index, row in branches.iterrows():
        if row["branch_id"] in br_update:
            branches.loc[index, "x"] = br_update[row["branch_id"]][0]
            branches.loc[index, "rateA"] = br_update[row["branch_id"]][1]
            # print(row['plant_id'],plant_update[row['plant_id']])
    branches = branches[-branches.branch_id.isin(br_delete)]
    return branches


if __name__ == "__main__":
    branches = pd.read_csv("output/branch.csv")
    br_update = {}
    br_delete = []

    par_branch = {}

    for br in branches.iloc:
        if br["branch_id"] < 990000:
            continue
        key = (br["from_bus_id"], br["to_bus_id"], br["rateA"])
        key = sort_tu(key)
        lis = [br["branch_id"], br["x"], br["rateA"]]

        if key in par_branch:
            par_branch[key].append(lis)
        else:
            par_branch[key] = [lis]

    for key in par_branch:
        num = len(par_branch[key])
        if num > 1:
            print(par_branch[key])
            lis = par_branch[key][0]
            br_update[lis[0]] = [lis[1] / num, lis[2] * num]
        for i in range(1, num):
            br_delete.append(par_branch[key][i][0])

    branches = update_branch(branches, br_update, br_delete)

    branches.to_csv("output/virtual/branch.csv", index=False)
