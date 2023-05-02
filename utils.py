import collections, math, os, sys, yaml

# This file contains some utility functions to help make the codebase cleaner
# Gets the first word from a string
def first_word(string: str) -> str:
    return string.split(" ")[0]

# Gets all words but the first from a string and joins them into a sentence
def get_remaining_words(string: str) -> str:
    return " ".join(string.split(" ")[1:])

# Loads a YAML config file (create parameter tells you if you should create the file if it doesn't exist)
def load_config_file(path: str, create: bool=False):
    # Creates file if it does not exist
    if not os.path.exists(path):
        if create:
            open(path, "w+")
        else:
            print(f"File {path} does not exist!")
            sys.exit()

    with open(path, "r+") as file:
        return yaml.safe_load(file)

# Gets an exponent form of an int
def to_exponent(num: int):
    powers = int(math.log10(num))

    return f"{round(num / (10 ** powers), 2)}e{powers}"

# Parses number to formatted string for printing the results
def to_formatted_string(num: int) -> str:
    return str(num) if num < 1e6 else f"{num} ({to_exponent(num)})"

# Class representing the main config file
class MainConfigFile:
    # Pass the yaml file from load_config_file
    def __init__(self, yaml_file):
        # Gets all data from the file
        self.stop_commands = yaml_file["stop commands"]
        self.use_already_has_items = yaml_file["use already has items"]
        self.current_pack = yaml_file["current pack"]
        self.addons = yaml_file["addons"]
        self.skip_resources = yaml_file["skip resources"]
        self.print_items_without_recipes = yaml_file["print items without recipes"]
        self.display_raw_materials = yaml_file["display all raw materials"]
        self.html_output = yaml_file["html output"]
        self.show_left_over_amount = yaml_file["show left over amount"]
        self.use_alt_sorting_method = yaml_file["use alternate sorting depth method"]

    # Gets the stop commands
    def get_stop_commands(self):
        return self.stop_commands

    # Gets if it should use items it already has
    def should_use_preexisting_items(self):
        return self.use_already_has_items

    # Gets the current pack
    def get_current_pack(self):
        return self.current_pack

    # Gets the list of addons
    def get_addons(self):
        return self.addons

    # Gets whether it should skip asking for resources the player has
    def should_skip_asking_existing_resources(self):
        return self.skip_resources

    # Gets whether calchelper should print which items don't have recipes
    def should_print_items_without_recipes(self):
        return self.print_items_without_recipes

    # Gets whether calchelper should always display all raw materials
    def should_display_raw_materials(self):
        return self.display_raw_materials

    # Gets whether the calculator should produce an HTML page representing the output
    def should_produce_html_output(self):
        return self.html_output

    # Gets whether the calculator should show left over amounts of items for crafts
    def should_show_left_over_amount(self):
        return self.show_left_over_amount

    # Gets whether the calculator should use the alternate sorting method
    def should_use_alternate_sorting_method(self):
        return self.use_alt_sorting_method

# Loads the main config file
def load_main_config():
    return MainConfigFile(load_config_file("app-config.yaml"))

# Class representing a pack config file
class PackConfigFile:
    # Pass the yaml file from load_config_file
    def __init__(self, yaml_file):
        self.items = {}

        if yaml_file is not None: # confirm the pack exists
            for key, value in yaml_file.items():
                if len(value["items"]) > 0: # can't have recipe with no inputs
                    self.items[key] = CraftingRecipe(key, [make_item_stack(item) for item in value["items"]], 1 if "produces" not in value else value["produces"])

    # Returns if the pack has a recipe for an item
    def has_recipe(self, item):
        return item in self.items

    # Deletes a recipe from the pack
    def delete_recipe(self, item):
        del self.items[item]

    # Gets the recipe for an item if it exists
    def get_recipe(self, item):
        if self.has_recipe(item):
            return self.items[item]
        else:
            return None

    # Sets a recipe
    def set_recipe(self, item, recipe):
        self.items[item] = recipe

    # Gets the set of raw materials
    def get_raw_materials(self):
        if not self.has_recipe("materials"):
            return set()
        else:
            return self.get_recipe("materials").get_item_types()

    # Adds a raw material to the pack
    def add_raw_material(self, material):
        if not self.has_recipe("materials"): # it may have to create the list of materials
            self.set_recipe("materials", CraftingRecipe("materials", [ItemStack(material)]))
        else:
            # Get the current materials recipe
            materials_recipe = self.get_recipe("materials")

            # We add the new itemstack to the end of the recipe
            self.set_recipe("materials", CraftingRecipe("materials", materials_recipe.get_inputs() + [ItemStack(material)]))

    # Gets the list of recipes
    def get_all_recipes(self):
        return self.items

    # Returns an key/value (item_name, recipe) iterable for all of the recipes
    def get_recipes_iterable(self):
        return self.items.items()

    # Extends a pack with an addon (in the form of another PackConfigFile)
    def extend_pack(self, addon: "PackConfigFile"):
        for item, recipe in addon.get_recipes_iterable():
            self.set_recipe(item, recipe)

    # Gets the depth of an item's recipe
    def get_recipe_depth(self, item):
        if self.has_recipe(item):
            return self.get_recipe(item).get_depth()
        else:
            return 0

# Loads a pack config file
def load_pack_config(path):
    return PackConfigFile(load_config_file(path, True))

# Class representing a crafting recipe in a pack
class CraftingRecipe:
    def __init__(self, output, inputs, produces=1):
        self.output = output
        self.produces = produces

        self.inputs = []

        inputs_dict = collections.defaultdict(int)

        # it does some processing for the inputs to add together cases where it calls for the same item twice
        for stack in inputs:
            name = stack.get_item_name()
            amount = stack.get_amount()

            inputs_dict[name] += amount

        for name, amount in inputs_dict.items():
            self.inputs.append(ItemStack(name, amount))

        # Depth is used for calculation, let's set to 0 for now
        self.depth = 0

    def __repr__(self):
        return f"{self.produces} {self.output}: {', '.join([str(i) for i in sorted(self.inputs, key=lambda i: i.get_item_name())])}"

    # Gets a set of all item types needed
    def get_item_types(self):
        return set([item.get_item_name() for item in self.inputs])

    # Gets the output of a recipe
    def get_output(self):
        return self.output

    # Gets the inputs of a recipe
    def get_inputs(self):
        return self.inputs

    # Gets how much of the item the recipe produces
    def get_amount_produced(self):
        return self.produces

    # Creates a recipe using the output ItemStack and inputs
    def create_with_itemstack(output, inputs):
        return CraftingRecipe(output.get_item_name(), inputs, output.get_amount())

    # Gets the recipe depth
    def get_depth(self):
        return self.depth

    # Sets the recipe depth
    def set_depth(self, depth):
        self.depth = depth

# Class representing a stack of items
class ItemStack:
    def __init__(self, item, amount=1, depth=0):
        self.item = item
        self.amount = amount

        # Depth can be used for ItemStacks for calculation purposes
        self.depth = depth

    def __repr__(self):
        return f"{self.amount} {self.item}"

    # Converts it to a string representation for displaying (separate from __repr__)
    def get_display_string(self):
        return f"{to_formatted_string(self.amount)} {self.item}"

    # Gets the name of the item
    def get_item_name(self):
        return self.item

    # Gets the item amount
    def get_amount(self):
        return self.amount

    # Gets the depth of the item within a recipe
    def get_depth(self):
        return self.depth

    # Adds to the amount of the item
    def add_amount(self, amount):
        self.amount += amount

# Gets an item stack from a string
def make_item_stack(string: str):
    amount = first_word(string)

    if amount.isnumeric():
        return ItemStack(get_remaining_words(string), int(amount))
    else:
        return ItemStack(string, 1)