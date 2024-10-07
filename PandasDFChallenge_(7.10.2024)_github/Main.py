import pandas as pd
from RangedEntitiesFinder import ranged_entity_finder as rEF

# Note: this is a slightly improved version of the previous attempt at this mini challenge.

if __name__ == "__main__":
    # Reading data from Excel into DataFrames.
    total_df = pd.read_excel(r"data/dataTables.xlsx", "total", converters={"id":str})
    sus_df = pd.read_excel(r"data/dataTables.xlsx", "sus", converters={"id":str})

    calcObj = rEF(total_df, sus_df)

    max_distance_from_target = input("Enter max distance from target in km (or enter 's' to stop the program): ")

    while max_distance_from_target != 's':
        try:
            calcObj.locate_closest_entities_to_target(float(max_distance_from_target))

        except ValueError:
            print("You didn't enter a float or entered 's'! Please try again.")
        
        max_distance_from_target = input("\nEnter max distance from target in km (or enter 's' to stop the program): ")