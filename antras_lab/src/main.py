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

def get_available_rooms(client: Any):
    occupied_rooms = get_occupied_rooms(client)
    cursor = client.find(
        collection = ACCOMMODATION_COLLECTION,
        search_query = {"room_number": {"$exists":True, "$nin": occupied_rooms}},
        projection_query = {"room_number": 1},
    )

    return [room["room_number"] for room in cursor]

def get_all_rooms(client: Any):
    cursor = client.find(
        collection = ACCOMMODATION_COLLECTION,
        search_query = {"room_number": {"$exists":True}},
        projection_query = {"room_number": 1},
    )

    return [room["room_number"] for room in cursor]

def get_all_guests(client: Any):
    cursor = client.find(
        collection = GUEST_COLLECTION,
        projection_query = {"name": 1, "surname": 1}
    )

    return [[guest["name"], guest["surname"]] for guest in cursor]

def view_guest_info(client: Any):
    guests = get_all_guests(client)

    guest_choices = [
        Choice(value = index, name = f"{name[0]} {name[1]}") for index, name in enumerate(guests)
    ]
    guest_index = inquirer.select(
        message = "Please select a guest:",
        choices = guest_choices
    ).execute()

    guest_info = list(client.find(
        collection = GUEST_COLLECTION,
        search_query = {"name": guests[guest_index][0], "surname": guests[guest_index][1]}
    ))[0]

    print(f"\nPrinting the info about the guest {guest_info['name']}...")
    print(f"{'name':<20}{guest_info['name']}")
    print(f"{'surname':<20}{guest_info['surname']}")
    print(f"{'phone number':<20}{guest_info['contacts']['phone']}")
    print(f"{'email addresss':<20}{guest_info['contacts']['email']}")
    print(f"{'occupied rooms':<20}{[key['room_number'] for key in guest_info['keys']]}")

def view_room_info(client: Any):
    room_keys = get_all_rooms(client)
    room_key = inquirer.select(
        message = "Please select a room:",
        choices = room_keys
    ).execute()

    room_info = list(client.find(
        collection = ACCOMMODATION_COLLECTION,
        search_query = {"room_number": room_key}
    ))[0]
    room_type_info = list(client.find(
        collection = ACCOMMODATION_COLLECTION,
        search_query = {"type_id": room_info["type_id"]}
    ))[0]

    print(f"\nPrinting the info about the room {room_key}...")
    print(f"{'room type':<20}{room_type_info['type']}")
    print(f"{'number of beds':<20}{room_type_info['beds']}")
    print(f"{'number of tv':<20}{room_type_info['tv']}")
    print(f"{'has pool':<20}{bool(room_type_info['tv'])}")
    print(f"{'price of the night':<20}{room_info['price']}")



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
                Choice(value = 1, name = "Get all the currently available rooms"),
                Choice(value = 2, name = "Get the total price of all occupied rooms (Aggregation Pipeline)"),
                Choice(value = 3, name = "Get the total price of all occupied rooms (MapReduce)"),
                Choice(value = 4, name = "View room info"),
                Choice(value = 5, name = "View guest info"),
            ]
        ).execute()


        if action == 0:
            occupied_rooms = get_occupied_rooms(hotel_db)
            if occupied_rooms:
                print("These are the currently occupied rooms:", occupied_rooms)
            else:
                print("There are no currently occupied rooms!")
        if action == 1:
            unoccupied_rooms = get_available_rooms(hotel_db)
            if unoccupied_rooms:
                print("These are the currently free rooms: ", unoccupied_rooms)
            else:
                print("There are no currently free rooms!")

        if action == 2:
            total_booking_price = get_total_booked_room_price_with_aggregate_pipeline(hotel_db)
            print("The currently occupied total price is:", total_booking_price)

        if action == 3:
            total_booking_price = get_total_booked_room_price_with_map_reduce(hotel_db)
            print("The currently occupied total price is:", total_booking_price)

        if action == 4:
            view_room_info(hotel_db)

        if action == 5:
            view_guest_info(hotel_db)

        print("\n" + "-"*40)
        proceed = inquirer.confirm(
            message="Would you like to query something else?",
        ).execute()
        if not proceed:
            break
        os.system('clear')


if __name__ == "__main__":   
  
   main()