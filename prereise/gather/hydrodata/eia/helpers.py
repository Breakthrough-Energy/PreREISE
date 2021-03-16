import pandas as pd


def scale_profile(profile, weight):
    """Scale hourly profile using a list of monthly weights.

    :param pandas.DataFrame profile: hourly profile.
    :param list weight: list of monthly weights.
    :return: (*pandas.DataFrame*) -- scaled hourly profile.
    :raises TypeError: if profile is not a time series or weight is not a list.
    :raises ValueError: if frequency of time series is not 1h or size of weight is
        not 12
    """
    if not isinstance(profile, pd.Series):
        raise TypeError("profile must be a pandas.Series object")
    if not isinstance(weight, list):
        raise TypeError("weight must be a list")
    if pd.infer_freq(profile.index) != "H":
        raise ValueError("frequency of time series must be 1h")
    if len(weight) != 12:
        raise ValueError("the list of weight must have exactly 12 elements")

    monthly_profile = profile.resample("M").sum(min_count=24 * 28)
    monthly_factor = [t / p for t, p in zip(weight, monthly_profile.values)]
    hourly_factor = (
        pd.Series(
            monthly_factor,
            index=pd.date_range(profile.index.min(), periods=12, freq="MS"),
        )
        .resample("H")
        .ffill()
        .reindex(profile.index, method="ffill")
    )

    return profile * hourly_factor
