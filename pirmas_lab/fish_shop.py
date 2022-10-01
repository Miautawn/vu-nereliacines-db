
from typing import Any, Optional, List
import os
import sys
import re
import json

from InquirerPy import inquirer
from InquirerPy.base.control import Choice

from redis_connector import Redis
from validators import (
    EXIT_CODE,
    check_for_exit_code,
    validate_product_key,
    validate_new_product_type,
    validate_new_product_type_description,
    validate_new_product_name,
    validate_new_product_price
)

# connecting to redis
redis = Redis.connect("127.0.0.1", 6379)

@check_for_exit_code
def _check_inventory(product_key: str) -> bool:
    return bool(redis.exists(product_key))

@check_for_exit_code
def _check_available_item_types(product_type: str) -> bool:
    return bool(redis.sismember("product_types", product_type))

def _get_available_product_keys() -> List[str]:
    product_keys = [item.decode("utf-8") for item in redis.keys("*:*")]
    return product_keys

def _get_available_item_types() -> List[str]:
    item_types = [item.decode("utf-8") for item in redis.smembers("product_types")]
    return item_types

def select_product_key() -> Optional[str]:
    available_product_keys = _get_available_product_keys()
    if not available_product_keys:
        print("Unfortunately, there are no registered products in DB, please add some!")
        return None

    product_key_choices = [ Choice(item) for item in available_product_keys ]
    product_key_choices.append(Choice(EXIT_CODE))
    product_key = inquirer.select(
        message="Select a product:",
        choices=product_key_choices
    ).execute()
    if product_key == EXIT_CODE:
        return None
    return product_key

def select_product_type_key() -> Optional[str]:
    available_item_types = _get_available_item_types()
    if not available_item_types:
        print("Unfortunately, there are no registered item types in the DB, please add some!")
        return None

    item_type_choises = [ Choice(item) for item in available_item_types ]
    item_type_choises.append(Choice(EXIT_CODE))
    item_type = inquirer.select(
        message="Select an item type:",
        choices=item_type_choises
    ).execute()
    if item_type == EXIT_CODE:
        return None
    return item_type

def ask_for_product_price(product_name: str = "") -> Optional[str]:
    product_price = inquirer.text(
        message=f"Enter the price of the new '{product_name}':",
        validate=validate_new_product_price,
        invalid_message="Invalid price! It must be a positive number"
    ).execute()
    if product_name == EXIT_CODE:
        return None
    return product_price

def insert_product_type() -> None:
    product_type = inquirer.text(
        message="Please enter a new product type:",
        validate=validate_new_product_type,
        invalid_message="Invalid new product type! It must not be empty or contain numbers!"
    ).execute()
    if product_type == EXIT_CODE:
        return None
    if _check_available_item_types(product_type):
        print("Unfortunately such product type already exists in the database!")
        return None

    product_description = inquirer.text(
        message="Please enter a new product description:",
        validate=validate_new_product_type_description,
        invalid_message="Invalid new product description! It can't be empty"
    ).execute()
    if product_description == EXIT_CODE:
        return None

    # add the product type to the product type set
    # and the description of the the type
    pipe = redis.pipeline()
    pipe.sadd("product_types", product_type)
    pipe.set(product_type, product_description)
    pipe.execute()

def insert_product() -> None:
    item_type = select_product_type_key()
    if item_type == None:
        return None
    
    product_name = inquirer.text(
        message=f"Enter the ID of the new '{item_type}':",
        validate=validate_new_product_name,
        invalid_message="Invalid new product name! It must be only integer numbers!"
    ).execute()
    if product_name == EXIT_CODE:
        return None
    if _check_inventory(f"{item_type}:{product_name}"):
        print("Unfortunately such product already exists!")
        return None

    product_price = ask_for_product_price(f"{item_type}:{product_name}")
    if not product_price:
        return None

    # set the item and its price
    redis.set(f"{item_type}:{product_name}", product_price)


def get_product_price(product_key: str) -> float:
    return float(redis.get(product_key))

def get_product_type_description(product_type_key: str):
    return redis.get(product_type_key).decode("utf-8")

def remove_product(product_key: str) -> None:
    redis.delete(product_key)

def change_product_price(product_key: str, price: str) -> None:
    redis.set(product_key, price)


def main() -> None:
    print("Welcome to the fish shop, manager!\n")
    while True:
        action = inquirer.select(
            message="Select an action:",
            choices=[
                Choice(value=0, name="Get the product type description"),
                Choice(value=1, name="Get the product price"),
                Choice(value=2, name="Insert a new product type"),
                Choice(value=3, name="Insert a new product"),
                Choice(value=4, name="Remove an existing product"),
                Choice(value=5, name="Change the price of an existing product"),
                Choice(value=None, name="Exit"),
            ],
        ).execute()

        if action == None:
            break
        elif action == 2:
            insert_product_type()
        elif action == 3:
            insert_product()
        elif action == 0:
            product_type_key = select_product_type_key()
            if product_type_key:
                description = get_product_type_description(product_type_key)
                print(f"The description of the '{product_type_key}' is: '{description}'")

        elif action == 1:
            product_key = select_product_key()
            if product_key:
                price = get_product_price(product_key)
                print(f"The price of the '{product_key}' is: {price}")

        elif action == 4:
            product_key = select_product_key()
            if product_key:
                remove_product(product_key)
                print(f"Removing {product_key}...DONE")
            
        elif action == 5:
            product_key = select_product_key()
            if product_key:
                product_price = ask_for_product_price(product_key)
                if product_price:
                    change_product_price(product_key, product_price)
                    print(f"Changed {product_key} price to {product_price}")
        
    
        print("-"*40)
        proceed = inquirer.confirm(
            message="Would you like to query something else?",
        ).execute()
        if not proceed:
            break
        os.system('clear')

if __name__ == "__main__":
    main()
    