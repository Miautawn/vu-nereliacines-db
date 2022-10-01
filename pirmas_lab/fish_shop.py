
from typing import Any
import os

from redis_connector import db

PRODUCT_TYPES = {
    1: "fishing_rod",
    2: "bait",
    3: "hook"
}

def _insert_product_with_price() -> None:
    macro = db.pipeline()
    product_key = _insert_product()
    _change_price(product_key)
    macro.execute()


def _insert_product() -> str:

    product_type_key = None
    brand = None
    print("Please select the type of product you wish to add!")
    product_type_selection = int(
        _ask_for_input(
    """
    1 - fishing_rod
    2 - bait
    3 - hook
    """
        )
    )

    product_type_key = PRODUCT_TYPES[product_type_selection]
    brand_selection_key = _ask_for_input("Please enter the brand of the product").strip()
    full_key = product_type_key + ':' + brand_selection_key
    print(f"Setting this key: {full_key}")    

    db.set(full_key, 0.0)
    return full_key


def _remove_product(key: str) -> None:
    db.delete(key)

def _get_product_price(key: str) -> float:
    return float(db.get(key))

def _change_price(key: str) -> None:
    new_price = _ask_for_input("Please enter a new price!")
    new_price = _validate_price(new_price)

    db.set(key, new_price)


def _check_inventory(key: str) -> bool:
    """
    Checks whether the key exists in redis
    """
    return 1 if db.exists(key) else 0

def _ask_for_input(message: str) -> str:
    print(message)
    return input(">> ")

def _validate_price(price: str) -> float:
    _clear_command_line()
    if _is_float(price):
        price = float(price)
        if price > 0.0:
            return price

    print("Unfortunately, the price is invalid :(")
    price = _ask_for_input("Please enter a valid price")
    return _validate_price(price)

def _is_float(number: Any) -> bool:
    try:
        float(number)
        return True
    except:
        return False

def _validate_key(key: str) -> str:
    _clear_command_line()
    if _check_inventory(key):
        return key

    print("Unfortunately, there is no such product with such a key :(")
    key = _ask_for_input("Please enter the key of your product (e.g. product-type:brand)")
    return _validate_key(key)

def _clear_command_line() -> None:
    os.system('clear')



print("Welcome to the fish shop, manager!")
while True:
    # _clear_command_line()
    print("Please select the command you wish to execute:")
    print("""
    1 - get the product price
    2 - insert a new product
    3 - insert a new product with price
    4 - remove an existing product
    5 - change a prace of an existing product
    """
    )
    response = int(input(">> "))

    if(response == 2):
        _insert_product()
        continue
    elif(response == 3):
        _insert_product_with_price()
        continue


    product_key = _ask_for_input("Please enter the key of your product (e.g. product-type:brand)")

    if(response == 1):
        product_key = _validate_key(product_key)
        price = _get_product_price(product_key)
        print(f"The price of the product {product_key} is {price}")
    elif(response == 4):
        product_key = _validate_key(product_key)
        _remove_product(product_key)
    elif(response == 5):
        product_key = _validate_key(product_key)
        _change_price(product_key)
    