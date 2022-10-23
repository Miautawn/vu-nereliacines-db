from typing import Any
import os

from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from bson.code import Code

from mongodb_utils import HotelMongoDBClient

CONNECTION_STRING = "mongodb://127.0.0.1:27017/"
DB_NAME = "fishing_resort_hotel"
ACCOMMODATION_COLLECTION = "accomodations"
GUEST_COLLECTION = "guests"
MAP_REDUCE_COLLECTION = "map_reduce"


def get_occupied_rooms(client: Any):
    cursor = client.find(
        collection = GUEST_COLLECTION,
        search_query = {},
        projection_query = {"keys": {"room_number": 1}}
    )

    occupied_rooms = []
    for doc in cursor:
        for key in doc["keys"]:
            occupied_rooms.append(key["room_number"])

    return occupied_rooms


def get_total_booked_room_price_with_aggregate_pipeline(client: Any):
    stage_lookup_rooms = {
        "$lookup": {
            "from": ACCOMMODATION_COLLECTION,
            "localField": "keys.room_number",
            "foreignField": "room_number",
            "as": "joined_rooms"
        }
    }
    stage_unwind_matched_rooms = {
        "$unwind": "$joined_rooms"
    }

    stage_group_and_sum = {
        "$group": {
            "_id": None,
            "total_booking_price": {"$sum": "$joined_rooms.price"}
        }
    }
    pipeline = [stage_lookup_rooms, stage_unwind_matched_rooms, stage_group_and_sum]
    result = list(client.aggregate(GUEST_COLLECTION, pipeline))[0]["total_booking_price"]
    return float(result)


def get_total_booked_room_price_with_map_reduce(client: Any):
    map_guest_function = Code(
        """
        function() {
            for (var i = 0; i < this.keys.length; i++) {
                emit(this.keys[i].room_number, 0.0);
            }
        }
        """
    )
    map_accomodation_function = Code(
        """
        function() {
            if(this.room_number !== undefined) {
                emit(this.room_number, this.price);
            }
        }
        """
    )

    map_joined_function = Code(
        """
        function() {
            if(this.value.joined !== undefined)
            emit(null, this.value.price)
        }
        """
    )

    reduce_function = Code(
        """
        function(key, values) {
            if (values.length == 1) {
                return values[0]
            }
            else {
                return {price: Array.sum(values), joined: true}
            }
        }
        """
    )

    # map_reduce the guest keys
    client.db.command(
        "mapReduce",
        value = GUEST_COLLECTION,
        map = map_guest_function,
        reduce = reduce_function,
        out = {"replace": MAP_REDUCE_COLLECTION}
    )

    # map_reduce the rooms and reduce them on repeating keys from keys
    client.db.command(
        "mapReduce",
        value = ACCOMMODATION_COLLECTION,
        map = map_accomodation_function,
        reduce = reduce_function,
        out = {"reduce": MAP_REDUCE_COLLECTION}
    )

    # do the final reduce to sum all the values
    result = client.db.command(
        "mapReduce",
        value = MAP_REDUCE_COLLECTION,
        map = map_joined_function,
        reduce = reduce_function,
        out = {"inline": 1}
    )

    return result["results"][0]["value"]["price"]

def main():

    # initialising DB
    hotel_db = HotelMongoDBClient(CONNECTION_STRING, DB_NAME)
    hotel_db.drop_db()

    db_backfill_conf = {
        ACCOMMODATION_COLLECTION: "src/data/accommodations_data.json",
        GUEST_COLLECTION: "src/data/guest_data.json"
    }

    hotel_db.seed_db(db_backfill_conf)

    # main program loop
    print("\nWelcome to the Fishing Resort Hotel management console!")
    while True:
        action = inquirer.select(
            message = "Select an action:",
            choices = [
                Choice(value = 0, name = "Get all the currently occupied rooms"),
                Choice(value = 1, name = "Get the total price of all occupied rooms (Aggregation Pipeline)"),
                Choice(value = 2, name = "Get the total price of all occupied rooms (MapReduce)"),
            ]
        ).execute()


        if action == 0:
            occupied_rooms = get_occupied_rooms(hotel_db)
            if occupied_rooms:
                print("These are the currently occupied rooms:", occupied_rooms)
            else:
                print("There are no currently occupied rooms!")

        if action == 1:
            total_booking_price = get_total_booked_room_price_with_aggregate_pipeline(hotel_db)
            print("The currently occupied total price is:", total_booking_price)

        if action == 2:
            total_booking_price = get_total_booked_room_price_with_map_reduce(hotel_db)
            print("The currently occupied total price is:", total_booking_price)

        print("\n" + "-"*40)
        proceed = inquirer.confirm(
            message="Would you like to query something else?",
        ).execute()
        if not proceed:
            break
        os.system('clear')


if __name__ == "__main__":   
  
   main()