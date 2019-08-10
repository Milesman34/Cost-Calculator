import re
import sys
import yaml

from collections import defaultdict
from typing import Any, Dict, List, Tuple


# Sanitizes the input string, removing leading, trailing, and excess spaces
def sanitize_input_string(input_string: str) -> str:
    return re.sub(r" {2,}", " ", input_string).strip()


# Deletes keys with a value of zero from a dictionary
def delete_zero_values(dict: Dict[Any, int]) -> Dict[Any, int]:
    return {key: value for key, value in dict.items() if value != 0}


# Subtracts 2 dictionaries from each other, using one that will be
# subtracted from and one that subtracts
def subtract_dictionaries(
        target: Dict[Any, int], subtracter: Dict[Any, int]) -> Tuple[Dict[Any, int], Dict[Any, int]]:
    for key, value in subtracter.items():
        if key in target:
            # The dictionaries have a common key, which will be compared to
            # determine what to do next
            if value > target[key]:
                subtracter[key] -= target[key]

                # Sets key to zero instead of deleting it so it can delete it
                # later
                target[key] = 0
            else:
                target[key] -= value
                subtracter[key] = 0

    # Deletes all values of zero from the dictionaries
    return delete_zero_values(target), delete_zero_values(subtracter)


# Adds two dictionaries together. It does not modify previously existing
# entries
def add_dictionaries(target: Dict, adder: Dict) -> Dict:
    result_dict = {}

    for key, value in target.items():
        result_dict[key] = value

    for key, value in adder.items():
        if key not in result_dict:
            result_dict[key] = value

    return result_dict


# Sorts a list of Stacks in descending order
def sort_stack_list(ls: List["Stack"]) -> List["Stack"]:
    return sorted(ls, key=lambda stack: stack.amount, reverse=True)


# Converts a dictionary to a list of Stacks
def convert_to_stack_list(dict: Dict[str, int]) -> List["Stack"]:
    return [Stack(item_type, amount) for item_type, amount in dict.items()]


# Splits an input into half in order to extract the amount and item type
# Throws an exception if it has the wrong format
def split_input(input: str) -> Tuple[int, str]:
    # Split version based on spaces used for checking
    split = sanitize_input_string(input).split(" ")

    # The resulting list does not contain all of the elements required due to
    # the string not having enough spaces
    if len(split) < 2:
        raise InputFormatException
    else:
        # Gets the amount and item type from the resultant list
        string_amount = split[0]

        # The remaining words make up the item type, and must be joined
        # together
        item_type = " ".join(split[1:])

        try:
            amount = int(string_amount)

            if amount < 0:
                raise InputNegativeException

        except ValueError:
            # Raises a value error if the string cannot be converted to an int
            raise ValueError

        return amount, item_type


# Gets the depth of a recipe
def get_depth(items: List[str], pack: Dict[str, Dict]) -> int:
    # The maximum depth will automatically be the final depth
    current_max_depth = 0

    for item in items:
        depth = 1

        amount, item_type = split_input(item)

        if item_type in pack:
            # The depth goes up for each layer
            depth += get_depth(pack[item_type]["items"], pack)

        # Updates the current maximum if needed
        if depth > current_max_depth:
            current_max_depth = depth

    return current_max_depth


# Exception raised when the input uses the wrong format
class InputFormatException(Exception):
    pass


# Exception raised when the input amount is a decimal or a negative number
class InputRangeException(Exception):
    pass


# Exception raised when the input amount is a negative number
class InputNegativeException(InputRangeException):
    pass


# Represents an amount of items
class Stack:
    def __init__(self, item_type: str, amount: int) -> None:
        self.item_type = item_type
        self.amount = amount

    def __repr__(self) -> str:
        return "{} {}".format(self.amount, self.item_type)


# Represents the cost-calculator app
class App:
    def __init__(self, path: str) -> None:
        self.config = self.load_config_file(path)

        # Gets the pack listed in the config
        self.pack = self.load_config_file(self.config["current pack"])

        self.stop_commands = self.config["stop commands"]
        self.use_already_has_items = self.config["use already has items"]

        # Stuff that isn't set immediately
        self.user_items: Dict[str, int] = {}
        self.already_has_items: Dict[str, int] = {}

        # Items already asked about
        self.items_asked_about: List[str] = []

    # Loads a YAML config file
    def load_config_file(self, path: str) -> Dict:
        with open(path, "r") as file:
            return yaml.safe_load(file)

    # Gets a list of items from the user via the command line
    def get_items_from_user(self,
                            start_string: str,
                            correct_format_text: str = "Make sure to use the format \"amount item_type\", where amount is an integer and item_type is a string.") -> Dict[str,
                                                                                                                                                                          int]:
        # Prints this string before getting inputs
        print("{}\n".format(start_string))

        # Count of all items currently inputted
        items_counter: defaultdict = defaultdict(int)

        while True:
            current_input = input("> ")

            # When the user inputs a stop command, it stops getting items
            if current_input in self.stop_commands:
                break

            try:
                amount, item_type = split_input(current_input)

                items_counter[item_type] += amount
            except Exception as exception:
                if isinstance(exception, InputFormatException):
                    # Handles the exception if the input was too short
                    print(
                        "The input was missing key elements! {}".format(correct_format_text))
                elif isinstance(exception, InputNegativeException):
                    # Handles the exception if the input was negative
                    print(
                        "The input number was negative! Make sure to make it positive.")
                else:
                    # The other error thrown is a ValueError, thrown if the
                    # string couldn't be converted to a number
                    print("The first part of the input could not be converted to an integer! {}".format(
                        correct_format_text))

                sys.exit()

        # Returns a new dictionary using the items in the counter
        return dict(items_counter)

    # Gets the user items from the user
    def get_user_items(self) -> Dict[str, int]:
        user_items = delete_zero_values(
            self.get_items_from_user("Enter items:"))

        print("")

        return user_items

    # Gets items that the user already has
    def get_already_has_items(self,
                              item_types: List[str],
                              first_items: bool = True,
                              last_items: bool = True) -> Dict[str,
                                                               int]:
        items_dict: Dict[str, int] = {}

        if first_items:
            print("Enter items you already have:\n")

        for item_type in item_types:
            # It does not want to ask about the same item type twice
            if item_type not in self.already_has_items and item_type not in self.items_asked_about:
                try:
                    amount = int(input("How many {}? ".format(item_type)))

                    if amount < 0:
                        raise ValueError
                except ValueError:
                    print("You must input a positive integer!")

                    sys.exit()

                items_dict[item_type] = amount

                self.items_asked_about.append(item_type)

        if last_items:
            print("")

        return delete_zero_values(
            add_dictionaries(
                self.already_has_items,
                items_dict))

    # Prints the user items
    def print_user_items(self):
        # List of stack items used for printing
        stack_items = convert_to_stack_list(self.user_items)

        # Prints the items needed for the recipe
        if len(stack_items) > 0:
            for item in sort_stack_list(stack_items):
                print(item)
        else:
            print("No items required!")

    # Loads the recipes from the current pack
    def load_recipes(self):
        for item_type, config in self.pack.items():
            # Depth is how many crafting recipes are required to reach the
            # deepest point of the recipe
            config["depth"] = get_depth(config["items"], self.pack)

            # Produces default value
            if "produces" not in config:
                config["produces"] = 1

            # Makes the items config easier to use
            config["parsed_items"] = [Stack(" ".join(item.split(" ")[1:]), int(
                item.split(" ")[0])) for item in config["items"]]

    # Gets the maximum depth in a list of items
    def get_max_depth(self, items: Dict[str, int]) -> int:
        max_depth = 0

        for item_type, amount in items.items():
            # Depth will automatically be zero if there aren't any more craftable items
            # Otherwise, it extracts the depth config
            if item_type in self.pack and self.pack[item_type]["depth"] > max_depth:
                max_depth = self.pack[item_type]["depth"]

        return max_depth

    # Returns a dictionary where lists of items are mapped to depths
    def form_depth_dictionary(
            self, items: Dict[str, int]) -> Dict[int, List[Stack]]:
        dct: defaultdict = defaultdict(list)

        for item_type, amount in items.items():
            depth = 0

            if item_type in self.pack:
                depth = self.pack[item_type]["depth"]

            dct[depth].append(Stack(item_type, amount))

        return dct

    # Calculates the costs of items
    def calculate_costs(self, items: Dict[str, int]) -> Dict[str, int]:
        max_depth = self.get_max_depth(items)

        # No items are craftable, so it returns instantly
        if max_depth == 0:
            return items
        else:
            while self.get_max_depth(items) > 0:
                depth_dictionary = self.form_depth_dictionary(items)

                # Processes items that have the deepest recipes
                for item in depth_dictionary[max_depth]:
                    if item.item_type in self.pack:
                        for sub_item in self.pack[item.item_type]["parsed_items"]:
                            if sub_item.item_type in self.pack:
                                depth_dictionary[self.pack[sub_item.item_type]["depth"]].append(Stack(sub_item.item_type, sub_item.amount * item.amount))
                            else:
                                depth_dictionary[0].append(Stack(sub_item.item_type, sub_item.amount * item.amount))
                    else:
                        depth_dictionary[0].append(Stack(item.item_type, item.amount))

                del depth_dictionary[max_depth]

                new_items = defaultdict(int)

                # Resets the items dictionary
                for _, depth_items in depth_dictionary.items():
                    for item in depth_items:
                        new_items[item.item_type] += item.amount

                if self.use_already_has_items:
                    self.already_has_items = app.get_already_has_items(
                        [item_type for item_type, _ in new_items.items()], first_items=False, last_items=False)

                    new_items, self.already_has_items = subtract_dictionaries(new_items, self.already_has_items)

                return self.calculate_costs(new_items)

        return {}

    # Runs the app
    def init(self):
        self.user_items = self.get_user_items()

        if self.use_already_has_items:
            # Gets items the user already has by using the list the user has
            # provided
            self.already_has_items = self.get_already_has_items(
                [item_type for item_type, _ in self.user_items.items()], last_items=False)

            # Subtracts items the user already has from the original items
            self.user_items, self.already_has_items = subtract_dictionaries(
                self.user_items, self.already_has_items)

        self.load_recipes()

        self.user_items = self.calculate_costs(self.user_items)

        print("")

        self.print_user_items()


# Start the program
if __name__ == "__main__":
    app = App("app-config.yaml")

    app.init()
