from geopy import distance as gpy_distance
import pandas as pd
import math

class ranged_entity_finder():
    total_df = pd.DataFrame # DataFrame that contains data about the path of entities including a target.
    sus_df = pd.DataFrame   # DataFrame that contains data about the path of the target.

    def __init__(self, total: pd.DataFrame, sus: pd.DataFrame):
        if total.shape[1] != 5 or sus.shape[1] != 5:
            raise ValueError("Table dimensions are incorrect!")

        self.total_df = total
        self.sus_df = sus

    '''
    Calculates the distance between two gives given points
    on Earth. Each points consists of three values,
    Latitude, Longitude, and height above the surface (in km).
    '''
    def _calc_distance(self, point_origin: tuple, point_destination: tuple) -> float:
        if point_origin == point_destination: return 0

        # Saving the latitude and longitude coordinates separately.
        horiz_coords_origin = (point_origin[0], point_origin[1])
        horiz_coords_destination = (point_destination[0], point_destination[1])

        # Calculting the distance between the latitude and longitude coordinates.
        horiz_distance = gpy_distance.geodesic(
            horiz_coords_origin, 
            horiz_coords_destination).km

        # Calculating the height difference between the points.
        vert_distance = point_destination[2] - point_origin[2]

        # Applying pythagoras theorm to calculate the distance between the two points.
        return math.sqrt(horiz_distance**2 + vert_distance**2)


    '''
    Locates the closest entities within a defined distance from the **sus**picious target.
    The distance is measured in km.
    '''
    def locate_closest_entities_to_target(self, distance_from_target = 1000.0) -> None:
        # Checking if distance is valid.
        if distance_from_target <= 0: 
            print("Max distance can't be smaller or equal to 0!")
            return

        # Finding the target Id to drop from total_df for easier navigation in the data.
        entity_id_to_filter = self.sus_df["id"][0]

        # Validating sus table.
        if all(self.sus_df["id"] != entity_id_to_filter):
            print("Sus table is invalid!")
            return

        # Removing (dropping) the data about the target from total_df to make working with the data easier.
        # The target might had been dropped since a previous user input during runtime.
        self.total_df = self.total_df[self.total_df["id"] != entity_id_to_filter]

        
        # Saving occurences of entities crossing paths with the target without timestamp relation.
        # Grouping according to timestamps is done later.
        path_crosses = self.total_df.merge(
            self.sus_df[["lat", "long", "height"]],
            on=["lat", "long", "height"])

        # Grouping the path crosses according to timestamps (by rising order), latitude, longitude, and height.
        path_crosses_grouped = path_crosses.groupby(by=["ts", "lat", "long", "height"])[["id"]].apply(dict).dropna()
        
        # Storing the coordinates (as points) as a Series of dictionary of tuples, stored in sus DataFrame.
        path_points_sus = self.sus_df.groupby(by=["ts"])[["lat", "long", "height"]].apply(dict)

        print("Format of coordinates: (latitude [deg], longitude [deg], height [km])\n")

        # Iterating over the path of the target entity.
        for current_ts in path_points_sus.keys():
            if current_ts not in path_crosses_grouped.index: continue

            # The current group of entities (except target) in the current timestamp.
            ts_group = path_crosses_grouped.loc[current_ts]

            # The current location of the target entity (sus).
            # path_points_sus[current_ts].values() gives a series of values where the left number
            # is an index and the right is the actual value that's needed.
            # val.values[0] gets the needed value.
            sus_location = tuple(float(val.values[0]) for val in path_points_sus[current_ts].values())

            # Previou timestamp is used for checking if the current timestamp was printed already.
            prev_ts = math.nan

            # Iterating over the group of entities which belong to the current timestamp.
            for current_entities in ts_group.items():
                distance_calculated = self._calc_distance(sus_location, current_entities[0])

                if distance_calculated >= distance_from_target: continue

                if prev_ts != current_ts:
                    print(f"---------- Timestamp {current_ts} ----------")
                    prev_ts = current_ts

                print(f"Entity(ies):", end=' ')

                # Note2self: asterisk before an iterable object (such as a list)
                #            in a print statement will print all the values in an object
                #            in a readable way. Example: [1, 2, 3] with sep=", "
                #            will be printed as: 1, 2, 3    
                # Function .values() created a Pandas Series which is turned into a list.
                # The [0] is used to read only the Ids of the entities, without the idexes of the series.
                print(*list(current_entities[1].values())[0], sep=", ", end=' ')
                print(f"is/are close to target ({round(distance_calculated, 3)} km)!\n" 
                    + f"Entity(ies) coordinates:\t{current_entities[0]}\nTarget coordinates:\t\t{sus_location}\n")