import os
import json

from InquirerPy import inquirer
from InquirerPy.base.control import Choice

from cassandra_utils import CassandraDBClient
from cassandra.query import BatchStatement, SimpleStatement


def _get_cities(db):
    query = "SELECT * FROM city"
    return list(db.query(query))


def _get_restaurants(db):
    query = "SELECT * FROM restaurant"
    return list(db.query(query))


def _get_chefs(db):
    query = "SELECT * FROM chef"
    return list(db.query(query))


def list_cities_in_country(db):
    countries = set([city.country for city in _get_cities(db)])
    country_choices = [Choice(country) for country in countries]

    country = inquirer.select(
        message="Select a country:", choices=country_choices
    ).execute()

    query = f"SELECT * FROM city_by_country WHERE country = '{country}'"
    return list(db.query(query))


def list_restaurants_in_city(db):
    cities = [city.city for city in _get_cities(db)]
    city_choices = [Choice(city) for city in cities]

    city = inquirer.select(message="Select a city:", choices=city_choices).execute()

    query = f"SELECT * FROM restaurant_by_city WHERE city = '{city}'"
    return list(db.query(query))


def list_chefs_in_restaurant(db):
    restaurants = [restaurant.restaurant for restaurant in _get_restaurants(db)]
    restaurant_choices = [Choice(restaurant) for restaurant in restaurants]

    restaurant = inquirer.select(
        message="Select a restourant:", choices=restaurant_choices
    ).execute()

    query = f"SELECT * FROM chef_by_restaurant WHERE restaurant = '{restaurant}'"
    return list(db.query(query))


def list_chefs_in_city(db):
    cities = [city.city for city in _get_cities(db)]
    city_choices = [Choice(city) for city in cities]

    city = inquirer.select(message="Select a city:", choices=city_choices).execute()

    query = f"SELECT * FROM chef_by_city WHERE city = '{city}'"
    return list(db.query(query))


def insert_chef(db):
    restorant_records = list(_get_restaurants(db))
    restaurants = [restaurant.restaurant for restaurant in restorant_records]
    cities = [city.city for city in restorant_records]

    restaurant_choices = [
        Choice(value=index, name=restaurant)
        for index, restaurant in enumerate(restaurants)
    ]
    index = inquirer.select(
        message="Select a restourant for the new chef:", choices=restaurant_choices
    ).execute()

    name = inquirer.text(message="Enter a chef's name").execute()
    surname = inquirer.text(message="Enter a chef's surname").execute()
    age = int(inquirer.text(message="Enter a chef's age").execute())
    restaurant = restaurants[index]
    city = cities[index]

    db.insert("chef", {"name": name, "surname": surname, "restaurant": restaurant, "age": age})
    db.insert("chef_by_restaurant", {"name": name, "surname": surname, "restaurant": restaurant, "age": age})
    db.insert("chef_by_city", {"city": city, "name": name, "surname": surname, "restaurant": restaurant, "age": age})

def main():
    db = CassandraDBClient()
    db.reset()

    print("\nWelcome to the Fishing Restaurant Chain management console!")
    while True:
        action = inquirer.select(
            message="Select an action:",
            choices=[
                Choice(value=0, name="View all the cities that have our restaurants"),
                Choice(value=1, name="View all the restaurants"),
                Choice(value=2, name="View all the chefs that work for our restaurants"),
                Choice(value=3, name="List all the restaurant cities in a country"),
                Choice(value=4, name="List all the restaurants in the city"),
                Choice(value=5, name="List all the chefs in the restaurant"),
                Choice(value=6, name="List all the chefs in the city"),
                Choice(value=7, name="Insert a new chef"),
            ],
        ).execute()

        if action == 0:
            cities = _get_cities(db)
            print(f"{'CITY':<20}{'COUNTRY':<20}{'POPULATION':<20}")
            print("-" * 60)
            for city in cities:
                print(f"{city.city:<20}{city.country:<20}{city.population:<20}")

        if action == 1:
            restaurants = _get_restaurants(db)
            print(
                f"{'RESTAURANT':<20}{'CITY':<20}{'ADDRESS':<20}{'DAILY CUSTOMERS':<20}"
            )
            print("-" * 80)
            for restaurant in restaurants:
                print(
                    f"{restaurant.restaurant:<20}{restaurant.city:<20}{restaurant.address:<20}{restaurant.daily_customers:<20}"
                )

        if action == 2:
            chefs = _get_chefs(db)
            print(f"{'NAME':<20}{'SURNAME':<20}{'RESTAURANT':<20}{'AGE':<20}")
            print("-" * 80)
            for chef in chefs:
                print(
                    f"{chef.name:<20}{chef.surname:<20}{chef.restaurant:<20}{chef.age:<20}"
                )

        if action == 3:
            cities = list_cities_in_country(db)
            print(f"{'CITY':<20}{'COUNTRY':<20}{'POPULATION':<20}")
            print("-" * 60)
            for city in cities:
                print(f"{city.city:<20}{city.country:<20}{city.population:<20}")

        if action == 4:
            restaurants = list_restaurants_in_city(db)
            print(
                f"{'RESTAURANT':<20}{'CITY':<20}{'ADDRESS':<20}{'DAILY CUSTOMERS':<20}"
            )
            print("-" * 80)
            for restaurant in restaurants:
                print(
                    f"{restaurant.restaurant:<20}{restaurant.city:<20}{restaurant.address:<20}{restaurant.daily_customers:<20}"
                )

        if action == 5:
            chefs = list_chefs_in_restaurant(db)
            print(f"{'NAME':<20}{'SURNAME':<20}{'RESTAURANT':<20}{'AGE':<20}")
            print("-" * 80)
            for chef in chefs:
                print(
                    f"{chef.name:<20}{chef.surname:<20}{chef.restaurant:<20}{chef.age:<20}"
                )

        if action == 6:
            chefs = list_chefs_in_city(db)
            print(f"{'NAME':<20}{'SURNAME':<20}{'RESTAURANT':<20}{'AGE':<20}")
            print("-" * 80)
            for chef in chefs:
                print(
                    f"{chef.name:<20}{chef.surname:<20}{chef.restaurant:<20}{chef.age:<20}"
                )

        if action == 7:
            insert_chef(db)

        print("\n" + "-" * 40)
        proceed = inquirer.confirm(
            message="Would you like to query something else?",
        ).execute()
        if not proceed:
            break
        os.system("clear")


if __name__ == "__main__":
    main()
