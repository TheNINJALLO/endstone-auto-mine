"""Utility functions for sword/weapon validation and combat."""
from endstone.inventory import ItemStack

SWORD_TYPES = [
    "wooden_sword",
    "stone_sword", 
    "iron_sword",
    "golden_sword",
    "diamond_sword",
    "netherite_sword",
]

# Max durability for each sword type
SWORD_DURABILITY = {
    "wooden_sword": 59,
    "stone_sword": 131,
    "iron_sword": 250,
    "golden_sword": 32,
    "diamond_sword": 1561,
    "netherite_sword": 2031,
}

# Base damage for each sword type
SWORD_DAMAGE = {
    "wooden_sword": 4,
    "stone_sword": 5,
    "iron_sword": 6,
    "golden_sword": 4,
    "diamond_sword": 7,
    "netherite_sword": 8,
}


def is_sword(item: ItemStack | None) -> bool:
    """Check if the given item is a sword."""
    if item is None:
        return False
    
    item_type = str(item.type)
    if not item_type:
        return False
    
    # Remove namespace if present
    if ":" in item_type:
        item_type = item_type.split(":")[-1]
    
    return item_type in SWORD_TYPES


def get_sword_damage(item: ItemStack) -> int:
    """Get the base damage for a sword."""
    if not is_sword(item):
        return 1  # Fist damage
    
    item_type = str(item.type)
    if ":" in item_type:
        item_type = item_type.split(":")[-1]
    
    return SWORD_DAMAGE.get(item_type, 1)


def get_sword_max_durability(item: ItemStack) -> int:
    """Get the maximum durability for a sword."""
    if not is_sword(item):
        return 0
    
    item_type = str(item.type)
    if ":" in item_type:
        item_type = item_type.split(":")[-1]
    
    return SWORD_DURABILITY.get(item_type, 0)


def find_sword_in_inventory(player) -> tuple[int, ItemStack] | None:
    """Find the best sword in player's inventory.
    
    Returns (slot_index, item) or None if no sword found.
    Prioritizes main hand, then hotbar, then rest of inventory.
    """
    inventory = player.inventory
    
    # Check main hand first
    main_hand = inventory.item_in_main_hand
    if is_sword(main_hand):
        # Main hand is slot -1 in our convention (we'll handle separately)
        return (-1, main_hand)
    
    # Check hotbar (slots 0-8)
    best_sword = None
    best_slot = -1
    best_damage = 0
    
    for slot in range(inventory.size):
        item = inventory.get_item(slot)
        if is_sword(item):
            damage = get_sword_damage(item)
            if damage > best_damage:
                best_damage = damage
                best_sword = item
                best_slot = slot
    
    if best_sword:
        return (best_slot, best_sword)
    
    return None
