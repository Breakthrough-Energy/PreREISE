def clean_substations(df, zone_dic):
    return df.query("STATE in @zone_dic and LINES != 0")
