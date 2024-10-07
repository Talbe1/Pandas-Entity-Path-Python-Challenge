import pandas as pd
from RangedEntitiesFinder import ranged_entity_finder as rEF

if __name__ == "__main__":
    # Reading data from Excel into DataFrames.
    total_df = pd.read_excel(r"data/dataTables.xlsx", "total")
    sus_df = pd.read_excel(r"data/dataTables.xlsx", "sus")

    calcObj = rEF(total_df, sus_df)

    calcObj.locate_closest_entities_to_target(1000)