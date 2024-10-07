from geopy import distance as gpy_distance
import pandas as pd
import math

class ranged_entity_finder():
    total_df = pd.DataFrame # DataFrame that contains data about the path of entities including a target.
    sus_df = pd.DataFrame   # DataFrame that contains data about the path of the target.

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
        horiz_distance = gpy_distance.geodesic(
            horiz_coords_origin, 
            horiz_coords_destination).km

        # Calculating the height difference between the points.
        vert_distance = point_destination[2] - point_origin[2]

        # Applying pythagoras theorm to calculate the distance between the two points.
        return math.sqrt(horiz_distance**2 + vert_distance**2)


    '''
    Returns a point in 3D space representing the coordinates of the current entity whose coordinates belong to.
    '''
    def _extract_point_from_row(self, givenRow: pd.DataFrame) -> tuple:
        # Validating given argument.
        if (givenRow.shape[0] != 5 or len(givenRow.shape) != 1):
            raise ValueError("DataFrame for single point data must be a single row and contain 3 coordinate values!")

        # Returning a tuple representing the coordinates.
        # Turns out that accessing a column in a single row DataFrame
        # will return the value in that column by itself, not a DataFrame object.
        # Also there's a conversion to float from Numpy float for easier printing of the actual numbers.
        return (float(givenRow["lat"]), float(givenRow["long"]), float(givenRow["height"]))


    '''
    Locates the closest entities within a defined distance from the **sus**picious target.
    The distance is measured in km.
    '''
    def locate_closest_entities_to_target(self, distance_from_target = 1000.0) -> None:
        # Checking if distance is valid.
        if distance_from_target <= 0: 
            print("Max distance can't be smaller or equal to 0!")
            return

        # Validating sus table.
        if len(self.sus_df.groupby(by=["id"])) > 1:
            print("Sus table is invalid!")
            return

        # Grouping the data by the Ids.
        total_df_grouped = self.total_df.groupby("id")

        # Finding the target Id to drop from total_df for easier navigation in the data.
        entity_id_to_filter = next(iter(self.sus_df.groupby("id").groups.keys()))

        # Removing (dropping) the data about the target from total_df to make working with the data easier.
        # The target might had been dropped since a previous user input during runtime.
        try: 
            self.total_df = self.total_df.drop(total_df_grouped.get_group(entity_id_to_filter).index)

        except KeyError: pass

        # Defining an accumulator DataFrame to save any occurences of entities crossing paths with the target entity.
        pathCrosses = pd.DataFrame();

        # Passing over the rows of the target entity path.
        for self.sus_df_idx, current_row in self.sus_df.iterrows():
            # Slicing the DataFrame according to the latitude, longitude, and height.
            # The coordinates need to match between an entity and the target.
            # Note2self: remember that the .loc function is written with square brackets ('[' and ']'),
            #            and NOT regular brackets like in functions. Holy sh*t that syntax is weird.
            pathCrosses = pd.concat([pathCrosses,
                      self.total_df.loc[    # < Here's the loc that retreives data from total_df.
                        # Matching latitude.
                       (self.total_df["lat"] == current_row["lat"])
                        # Matching longitude.
                     & (self.total_df["long"] == current_row["long"])
                        # Matching height.
                     & (self.total_df["height"] == current_row["height"])]],
                      ignore_index = True)


        # Storing the coordinates (as points) as a list of tuples, stored in sus DataFrame.
        path_points_sus = list()
        for sus_path_idx, current_row in self.sus_df.iterrows():

            try: path_points_sus.append(self._extract_point_from_row(current_row))
            except ValueError:
                print("Invalid DataFrame dimensions! Aborting calculations...")
                return


        # Storing the coordinates (as points) as a dictionary of a list of tuples, stored in total DataFrame
        # (not including the target entity).
        # Structure of dictionary: keys are points, and the lists contain all entities (without the target) that
        # were at those coordinates at some point in time.
        path_points_crosses = dict()
        for path_crosses_idx, current_row in pathCrosses.iterrows():
            # Current point on the path of the target.
            try: current_cross_point = self._extract_point_from_row(current_row)
            except ValueError:
                print("Invalid DataFrame dimensions! Aborting calculations...")
                return

            # Check if the point was already added to the dictionary.
            if current_cross_point not in path_points_crosses:
                path_points_crosses[current_cross_point] = list()

            # Adding the entity Id to the dictionary.
            path_points_crosses[current_cross_point].append(current_row["id"])

        print("Format of coordinates: (latitude [deg], longitude [deg], height [km])\n")

        # Iterating over the previously created dictonary (path_points_crosses), whose keys are
        # points (current_cross_point), and entity Ids list is (current_entities_group).
        for current_cross_point, current_entities_group in path_points_crosses.items():
            # Iterating over the points in path of the target.
            for current_sus_point in path_points_sus:
                # There's no point in calculating the distance between points if they're the same...
                if current_sus_point == current_cross_point: continue

                # Catching except for invalid data.
                try: distance_calculated = self._calc_distance(current_sus_point, current_cross_point)
                except ValueError:
                    print("Error! Some data is invalid! A point or more missing 3 coordinate values! Continuing...")
                    continue

                # Checking if actual distance between entity and target is below the maximum allowed.
                if distance_calculated < distance_from_target:
                    print("Entity(ies):", end=' ')
                    # Note2self: asterisk before an iterable object (such as a list)
                    #            in a print statement will print all the values in an object
                    #            in a readable way. Example: [1, 2, 3] with sep=", "
                    #            will be printed as: 1, 2, 3
                    print(*current_entities_group, sep=", ", end=' ')
                    print(f"is/are close to target ({round(distance_calculated, 3)} km)!\n" 
                          + f"Entity(ies) coordinates:\t{current_cross_point}\nTarget coordinates:\t\t{current_sus_point}\n")