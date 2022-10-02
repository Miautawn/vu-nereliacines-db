
from typing import Callable, Any, Optional
import re
EXIT_CODE = "exit"

def check_for_exit_code(function: Callable) -> Callable:
    def inside(message: str) -> bool:
        if message == EXIT_CODE:
            return True
        return function(message)
    return inside
    
@check_for_exit_code
def validate_product_key(key: str) -> bool:
    return True if key and ':' in key else False

@check_for_exit_code
def validate_product_type_key(key: str) -> bool:
    return True if key and ':' not in key else False

@check_for_exit_code
def validate_new_product_type(product_type: str) -> bool:
    if (
        product_type
        and ':' not in product_type
        and not bool(re.search(r"\d", product_type))
    ):
        return True
    else:
        return False

@check_for_exit_code
def validate_new_product_type_description(product_description: str) -> bool:
    return True if product_description else False

@check_for_exit_code
def validate_new_product_name(product_name: str) -> bool:
    return product_name.isdigit()

@check_for_exit_code
def validate_new_product_price(price: str) -> bool:
    if _is_float(price):
        if float(price) > 0.0:
            return True
    return False

def _is_float(number: Any) -> bool:
    try:
        float(number)
        return True
    except:
        return False

