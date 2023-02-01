import numpy as np

from prereise.gather.demanddata.bldg_electrification import const


class LoadProjectionScenario:
    """Define load projection scenario for a load zone.
    For a base scenario, read and save building stock inputs.
    For a projection scenario, some fields are projected from base scenario
    based on the projection scenario inputs.

    :param str id: id of scenario, 'base' refers to modeled base year scenario
    :param pandas.Series input_series: precomputed information of building stock floor
        area and energy usages for a base scenario. User defined growth inputs for a
        projection scenario. This series contains information for a load zone,
        which are listed as follows:
        1) population
        2) total building floor area by type
        3) primary energy source types and household fraction for space heating,
           cooling, hot water and cooking
        4) assumed dominate type of heat pump
        5) assumed energy efficiency of cooking and air conditioning.
    :param load_projection_scenario.LoadProjectionScenario other: the base scenario
        instance for a projection scenario creation. None if creating a base scenario.
    """

    def __init__(self, id, input_series, other=None):
        self.id = id
        self.year = int(input_series["year"])
        self.hp_type_heat = input_series.pop("heat_hp_type")
        self.hp_type_dhw = input_series.pop("dhw_hp_type")
        self.cook_efficiency = input_series.pop("cook_eff")
        input_series = input_series.astype("float64")
        self.cool_energy_intensity = input_series["cool_energy_intensity(relative)"]
        self.stats = input_series
        if other is None:
            self.stats = (
                input_series.dropna()
            )  # drop rows that only used for defining future scenarios
            self._compute_base_scenario()

        else:
            self._compute_project_scenario(other)

    def _compute_base_scenario(self):
        self.pop = self.stats["pop"]
        self.floor_area_m2 = {
            "res": self.stats["res_area_m2"],
            "com": self.stats["com_area_m2"],
        }
        self.hp_heat_area_m2 = (
            self.stats["frac_hp_res_heat"] * self.floor_area_m2["res"]
            + self.stats["frac_hp_com_heat"] * self.floor_area_m2["com"]
        )
        self.hp_heat_frac = self.hp_heat_area_m2 / (
            self.floor_area_m2["res"] + self.floor_area_m2["com"]
        )
        self.resist_heat_area_m2 = (
            self.stats["frac_resist_res_heat"] * self.floor_area_m2["res"]
            + self.stats["frac_resist_com_heat"] * self.floor_area_m2["com"]
        )
        self.resist_heat_frac = self.resist_heat_area_m2 / (
            self.floor_area_m2["res"] + self.floor_area_m2["com"]
        )
        self.elec_cool_m2 = (
            self.stats["frac_elec_res_cool"] * self.floor_area_m2["res"]
            + self.stats["frac_elec_com_cool"] * self.floor_area_m2["com"]
        )

    def _compute_project_scenario(self, other):
        self.pop = other.pop * (1 + self.stats["pop_ann_grow_rate"]) ** (
            self.year - other.year
        )
        self.floor_area_m2 = {}
        for clas in const.classes:
            if np.isnan(self.stats[f"{clas}_area_ann_grow_rate"]):
                # floor area growth rate is assumed to be proportional to population
                # growth by default, unless user defines a growth rate for floor area
                self.floor_area_m2[clas] = other.floor_area_m2[clas] * (
                    1 + self.stats["pop_ann_grow_rate"]
                ) ** (self.year - other.year)
            else:
                self.floor_area_m2[clas] = other.floor_area_m2[clas] * (
                    1 + self.stats[f"{clas}_area_ann_grow_rate"]
                ) ** (self.year - other.year)

            if not np.isnan(self.stats[f"frac_hp_{clas}_heat"]):
                # calculate fraction of floor area using heat pump, resistance heat
                # or fossil fuel furnace as major heating appliances
                # Users can either define the fractions directly or the shift in major
                # heating fuels from the base scenario or assume BAU cases
                self.stats[f"ff2hp_{clas}"] = (
                    1
                    - self.stats[f"frac_ff_{clas}_heat"]
                    / other.stats[f"frac_ff_{clas}_heat"]
                )
            elif not np.isnan(self.stats[f"ff2hp_{clas}"]):
                self.stats[f"frac_hp_{clas}_heat"] = (
                    other.stats[f"frac_hp_{clas}_heat"]
                    + other.stats[f"frac_resist_{clas}_heat"]
                    * self.stats[f"resist2hp_{clas}"]
                    + other.stats[f"frac_ff_{clas}_heat"] * self.stats[f"ff2hp_{clas}"]
                )
                self.stats[f"frac_resist_{clas}_heat"] = other.stats[
                    f"frac_resist_{clas}_heat"
                ] * (1 - self.stats[f"resist2hp_{clas}"])
                self.stats[f"frac_ff_{clas}_heat"] = other.stats[
                    f"frac_ff_{clas}_heat"
                ] * (1 - self.stats[f"ff2hp_{clas}"])
            else:
                self.stats[f"frac_hp_{clas}_heat"] = other.stats[f"frac_hp_{clas}_heat"]
                self.stats[f"frac_resist_{clas}_heat"] = other.stats[
                    f"frac_resist_{clas}_heat"
                ]
                self.stats[f"frac_ff_{clas}_heat"] = other.stats[f"frac_ff_{clas}_heat"]
                self.stats[f"ff2hp_{clas}"] = 0
                self.stats[f"resist2hp_{clas}"] = 0

            if np.isnan(self.stats[f"frac_elec_{clas}_cool"]):
                self.stats[f"frac_elec_{clas}_cool"] = other.stats[
                    f"frac_elec_{clas}_cool"
                ]
            if np.isnan(self.stats[f"frac_ff_dhw_{clas}"]):
                self.stats[f"frac_ff_dhw_{clas}"] = other.stats[f"frac_ff_dhw_{clas}"]
            cook_other = "cook" if clas == "com" else "other"
            if np.isnan(self.stats[f"frac_ff_{cook_other}_{clas}"]):
                self.stats[f"frac_ff_{cook_other}_{clas}"] = other.stats[
                    f"frac_ff_{cook_other}_{clas}"
                ]

        self.hp_heat_area_m2 = (
            self.stats["frac_hp_res_heat"] * self.floor_area_m2["res"]
            + self.stats["frac_hp_com_heat"] * self.floor_area_m2["com"]
        )

        self.hp_heat_frac = self.hp_heat_area_m2 / (
            self.floor_area_m2["res"] + self.floor_area_m2["com"]
        )
        self.resist_heat_area_m2 = (
            self.stats["frac_resist_res_heat"] * self.floor_area_m2["res"]
            + self.stats["frac_resist_com_heat"] * self.floor_area_m2["com"]
        )
        self.resist_heat_frac = self.resist_heat_area_m2 / (
            self.floor_area_m2["res"] + self.floor_area_m2["com"]
        )
        self.elec_cool_m2 = (
            self.stats["frac_elec_res_cool"] * self.floor_area_m2["res"]
            + self.stats["frac_elec_com_cool"] * self.floor_area_m2["com"]
        )

    def floor_area_growth(self, other):
        """
        :return (*float*) -- compound floor area growth
        """
        return (self.floor_area_m2["res"] + self.floor_area_m2["com"]) / (
            other.floor_area_m2["res"] + other.floor_area_m2["com"]
        )

    def floor_area_growth_type(self, other, clas):
        """
        :return (*float*) -- compound floor area growth by building type
        """
        return self.floor_area_m2[clas] / other.floor_area_m2[clas]

    def frac_hp_growth(self, other):
        """
        :return (*float*) -- floor area growth ratio that use hp as main heating
            appliance
        """
        return self.hp_heat_area_m2 / other.hp_heat_area_m2

    def frac_resist_growth(self, other):
        """
        :return (*float*) -- floor area growth ratio that use resistance heat as main
            heating source
        """
        return self.resist_heat_area_m2 / other.resist_heat_area_m2

    def frac_cool_growth(self, other):
        """
        :return (*float*) -- floor area growth ratio that have electric air conditioning
        """
        return self.elec_cool_m2 / other.elec_cool_m2

    def frac_htg_ff2hp(self, other, clas):
        """
        :return (*float*) -- fraction of floor area electrified for heating
        """
        return other.stats[f"frac_ff_{clas}_heat"] - self.stats[f"frac_ff_{clas}_heat"]

    def frac_dhw_ff2hp(self, other, clas):
        """
        :return (*float*) -- fraction of floor area electrified for dhw
        """
        return other.stats[f"frac_ff_dhw_{clas}"] - self.stats[f"frac_ff_dhw_{clas}"]

    def frac_cook_ff2hp(self, other, clas):
        """
        :return (*float*) -- fraction of floor area electrified for cooking
        """
        cook_other = "cook" if clas == "com" else "other"
        return (
            other.stats[f"frac_ff_{cook_other}_{clas}"]
            - self.stats[f"frac_ff_{cook_other}_{clas}"]
        )

    def frac_cooling_eff_change(self, other):
        """
        :return (*float*) -- ratio of cooling efficiency improvement compares to base
            scenario
        """
        return self.cool_energy_intensity / other.cool_energy_intensity

    def compare_hp_heat_type(self, other):
        """
        :return (*bool*) -- True if the heat pump type for projection scenario is the
            same as that of base scenario, otherwise False
        """
        return self.hp_type_heat == other.hp_type_heat
