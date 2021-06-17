import glob

import pandas as pd

coord_precision = ".9f"


def get_exce():
    global wei_zhi

    all_exce = glob.glob("overloading*.csv")
    if len(all_exce) == 0:
        return 0
    else:
        for i in range(len(all_exce)):
            print(all_exce[i])
        return all_exce


if __name__ == "__main__":
    all_exce = get_exce()
    violation = pd.DataFrame(
        columns=["branchid", "trans_viol", "branch_rating", "percentage"]
    )
    for csv in all_exce:
        df1 = pd.read_csv(csv)
        violation = violation.append(df1)
    violation = violation[violation["percentage"] > 0.01]
    vio_branches = violation.groupby("branchid")["trans_viol"].max().reset_index()
    br_vio = vio_branches.set_index("branchid")["trans_viol"].to_dict()

    branches = pd.read_csv("branch.csv")

    new_branch_id = 800001
    add_branch = {}
    for br in branches.iloc:
        if br["branch_id"] in br_vio:
            num = int(br_vio[br["branch_id"]] / br["rateA"]) + 1
            add_branch[new_branch_id] = [
                br["from_bus_id"],
                br["to_bus_id"],
                br["rateA"] * num,
                br["interconnect"],
                br["x"] / num,
            ]
            new_branch_id = new_branch_id + 1

    for br in add_branch:
        new = pd.DataFrame(
            {
                "branch_id": br,
                "from_bus_id": add_branch[br][0],
                "to_bus_id": add_branch[br][1],
                "r": 0,
                "x": add_branch[br][4],
                "b": 0,
                "rateA": add_branch[br][2],
                "rateB": 0,
                "rateC": 0,
                "ratio": 0,
                "angle": 0,
                "status": 0,
                "angmin": 0.0,
                "angmax": 0.0,
                "Pf": 0.0,
                "Qf": 0.0,
                "Qt": 0.0,
                "mu_Sf": 0.0,
                "mu_St": 0.0,
                "mu_angmin": 0.0,
                "mu_angmax": 0.0,
                "branch_device_type": "Line",
                "interconnect": add_branch[br][3],
            },
            index=[1],
        )
        branches = branches.append(new)

    branches.to_csv("branch.csv", index=False)
