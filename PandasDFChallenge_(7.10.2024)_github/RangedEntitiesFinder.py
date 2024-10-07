import geopy.distance
import pandas as pd
import math
import openpyxl

class ranged_entity_finder():
    total_df = pd.DataFrame
    sus_df = pd.DataFrame

    def __init__(self, total: pd.DataFrame, sus: pd.DataFrame):
        self.total_df = total
        self.sus_df = sus

    '''
    Calculates the distance between two gives given points
    on Earth. Each points consists of three values,
    Latitude, Longitude, and height above the surface (in km).
    '''
    def _calc_distance(self, point_origin: tuple, point_destination: tuple):
        # Each point must contain 3 coordinate values for the
        # calculation to work properly.
        if len(point_origin) != 3 | len(point_destination) != 3:
            raise ValueError("Point must contain 3 coordinate values!")

        # Saving the latitude and longitude coordinates separately.
        horiz_coords_origin = (point_origin[0], point_origin[1])
        horiz_coords_destination = (point_destination[0], point_destination[1])

        # Calculting the distance between the latitude and longitude coordinates.
        horiz_distance = geopy.distance.geodesic(
            horiz_coords_origin, 
            horiz_coords_destination).km

        # Calculating the height difference between the points.
        vert_distance = point_destination[2] - point_origin[2]

        # Applying pythagoras theorm to calculate the distance between the two points.
        return math.sqrt(horiz_distance**2 + vert_distance**2)


    '''
    Returns a point in 3D space representing the coordinates of the current entity whose coordinates belong to.
    '''
    def _extract_point_from_row(self, givenRow: pd.DataFrame):
        # Validating given argument.
        if (givenRow.shape[0] != 5 or len(givenRow.shape) != 1):
            raise ValueError("DataFrame for single point data must be a single row and contain 3 coordinate values!")

        # Returning a tuple representing the coordinates.
        # Turns out that accessing a column in a single row DataFrame
        # will return the value in that column by itself, not a DataFrame object.
        return (givenRow["lat"], givenRow["long"], givenRow["height"])


    '''
    Locates the closest entities within a defined distance from the **sus**picious target.
    The distance is measured in km.
    '''
    def locate_closest_entities_to_target(self, distance_from_target = 1000.0):
        print(self.sus_df)
        
        # Validating sus table.
        if len(self.sus_df.groupby(by=["id"])) > 1:
            print("Sus table is invalid!")
            return

        # Grouping the data by the Ids.
        total_df_grouped = self.total_df.groupby("id")
    
        # Finding the target Id to drop from total_df for easier navigation in the data.
        entity_id_to_filter = next(iter(self.sus_df.groupby("id").groups.keys()))

        # Removing (dropping) the data about the target from total_df to make working with the data easier.
        self.total_df = self.total_df.drop(total_df_grouped.get_group(entity_id_to_filter).index)

        # Defining an accumulator DataFrame to save any occurences of entities crossing paths with the target entity.
        pathCrosses = pd.DataFrame();

        # Passing over the rows of the target entity path.
        for self.sus_df_idx, current_row in self.sus_df.iterrows():
            # Slicing the DataFrame according to the latitude, longitude, and height.
            # The coordinates need to match between an entity and the target.
            # Note2self: remember that the .loc function is written with square brackets ('[' and ']'),
            #            and NOT regular brackets like in functions. Holy sh*t that syntax is weird.
            pathCrosses = pd.concat([pathCrosses,
                        # Matching latitude.
                      self.total_df.loc[(self.total_df["lat"] == current_row["lat"])
                        # Matching longitude.
                     & (self.total_df["long"] == current_row["long"])
                        # Matching height.
                     & (self.total_df["height"] == current_row["height"])]],
                      ignore_index = True)


        # Storing the coordinates (as points) as a list of tuples, stored in sus DataFrame.
        path_points_sus = list()
        for sus_path_idx, current_row in self.sus_df.iterrows():
            path_points_sus.append(self._extract_point_from_row(current_row))


        # Storing the coordinates (as points) as a list of tuples, stored in total DataFrame
        # (not including the target entity).
        path_points_crosses = dict()
        for path_crosses_idx, current_row in pathCrosses.iterrows():
            if int(current_row["id"]) not in path_points_crosses:
                path_points_crosses[int(current_row["id"])] = list()

            path_points_crosses[int(current_row["id"])].append(self._extract_point_from_row(current_row))


        # Iterating over the points of path of sus.
        for current_sus_point in path_points_sus:
            # Iterating over the entities who crossed paths with the target (sus) entity.
            for current_crossing_entity in path_points_crosses.items():
                # Iterating over the points of path crossings of a single entity with the target.
                for current_cross_point in current_crossing_entity[1]:
                    # Checking if the points are different because timestamp isn't the same.
                    if current_sus_point != current_cross_point and self._calc_distance(current_sus_point, current_cross_point) < distance_from_target:
                        print(f"Entity {current_crossing_entity[0]} is close to target {self._calc_distance(current_sus_point, current_cross_point)}! Entity: {current_cross_point}, target: {current_sus_point}\n")





