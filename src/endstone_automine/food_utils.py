"""Utility functions for food detection and consumption."""
from endstone.inventory import ItemStack

# Food items with their hunger restoration values (in half-hunger-bars)
FOOD_ITEMS = {
    # Cooked meats (best)
    "cooked_beef": 8,
    "cooked_porkchop": 8,
    "cooked_mutton": 6,
    "cooked_chicken": 6,
    "cooked_rabbit": 5,
    "cooked_cod": 5,
    "cooked_salmon": 6,
    
    # Other good foods
    "golden_apple": 4,
    "enchanted_golden_apple": 4,
    "golden_carrot": 6,
    "bread": 5,
    "baked_potato": 5,
    "pumpkin_pie": 8,
    "cake": 2,  # Per slice
    "rabbit_stew": 10,
    "mushroom_stew": 6,
    "beetroot_soup": 6,
    "suspicious_stew": 6,
    
    # Raw foods (less effective)
    "beef": 3,
    "porkchop": 3,
    "mutton": 2,
    "chicken": 2,  # Can cause hunger
    "rabbit": 3,
    "cod": 2,
    "salmon": 2,
    "tropical_fish": 1,
    
    # Vegetables and fruits
    "apple": 4,
    "carrot": 3,
    "potato": 1,
    "beetroot": 1,
    "melon_slice": 2,
    "sweet_berries": 2,
    "glow_berries": 2,
    "dried_kelp": 1,
    
    # Other
    "cookie": 2,
    "rotten_flesh": 4,  # Can cause hunger
    "spider_eye": 2,  # Poisonous
    "honey_bottle": 6,
}

# Foods to avoid if possible (can cause negative effects)
RISKY_FOODS = {"chicken", "rotten_flesh", "spider_eye", "pufferfish", "poisonous_potato"}


def is_food(item: ItemStack | None) -> bool:
    """Check if the given item is food."""
    if item is None:
        return False
    
    item_type = str(item.type)
    if not item_type:
        return False
    
    # Remove namespace if present
    if ":" in item_type:
        item_type = item_type.split(":")[-1]
    
    return item_type in FOOD_ITEMS


def get_food_value(item: ItemStack) -> int:
    """Get the hunger restoration value for a food item."""
    if not is_food(item):
        return 0
    
    item_type = str(item.type)
    if ":" in item_type:
        item_type = item_type.split(":")[-1]
    
    return FOOD_ITEMS.get(item_type, 0)


def is_risky_food(item: ItemStack) -> bool:
    """Check if the food has negative side effects."""
    if not is_food(item):
        return False
    
    item_type = str(item.type)
    if ":" in item_type:
        item_type = item_type.split(":")[-1]
    
    return item_type in RISKY_FOODS


def find_food_in_inventory(player, avoid_risky: bool = True) -> tuple[int, ItemStack] | None:
    """Find the best food in player's inventory.
    
    Returns (slot_index, item) or None if no food found.
    Prioritizes cooked meats and high-value foods.
    """
    inventory = player.inventory
    
    best_food = None
    best_slot = -1
    best_value = 0
    
    for slot in range(inventory.size):
        item = inventory.get_item(slot)
        if is_food(item):
            # Skip risky foods if requested
            if avoid_risky and is_risky_food(item):
                continue
            
            value = get_food_value(item)
            if value > best_value:
                best_value = value
                best_food = item
                best_slot = slot
    
    if best_food:
        return (best_slot, best_food)
    
    # If no safe food, try risky foods as last resort
    if avoid_risky:
        return find_food_in_inventory(player, avoid_risky=False)
    
    return None


def consume_food(player, slot: int) -> bool:
    """Consume one food item from the given inventory slot.
    
    Returns True if food was consumed, False otherwise.
    """
    inventory = player.inventory
    item = inventory.get_item(slot)
    
    if not is_food(item):
        return False
    
    # Reduce stack by 1
    if item.amount > 1:
        item.amount -= 1
        inventory.set_item(slot, item)
    else:
        # Remove the item entirely
        inventory.set_item(slot, ItemStack("minecraft:air", 0))
    
    return True
