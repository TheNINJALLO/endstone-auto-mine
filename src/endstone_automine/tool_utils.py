"""Utility functions for pickaxe validation and enchantment handling."""
import random
from endstone.inventory import ItemStack

PICKAXE_TYPES = [
    "wooden_pickaxe",
    "stone_pickaxe",
    "iron_pickaxe",
    "golden_pickaxe",
    "diamond_pickaxe",
    "netherite_pickaxe",
]

# Max durability for each pickaxe type
PICKAXE_DURABILITY = {
    "wooden_pickaxe": 59,
    "stone_pickaxe": 131,
    "iron_pickaxe": 250,
    "golden_pickaxe": 32,
    "diamond_pickaxe": 1561,
    "netherite_pickaxe": 2031,
}

# Enchantment string IDs (compatible with all Endstone versions)
ENCHANT_SILK_TOUCH = "minecraft:silk_touch"
ENCHANT_FORTUNE = "minecraft:fortune"
ENCHANT_EFFICIENCY = "minecraft:efficiency"
ENCHANT_UNBREAKING = "minecraft:unbreaking"


def normalize_item_type(item_type: str) -> str:
    """Strip namespace from item type."""
    return item_type.lower().replace("minecraft:", "")


def is_pickaxe(item: ItemStack | None) -> bool:
    """Check if the item is a pickaxe."""
    if item is None:
        return False
    item_type = normalize_item_type(str(item.type))
    return any(p in item_type for p in PICKAXE_TYPES)


def get_max_durability(item: ItemStack) -> int:
    """Get max durability for a pickaxe."""
    item_type = normalize_item_type(str(item.type))
    for pick_type, durability in PICKAXE_DURABILITY.items():
        if pick_type in item_type:
            return durability
    return 1000  # Fallback


def get_remaining_durability(item: ItemStack) -> int:
    """Get remaining uses before tool breaks."""
    max_dur = get_max_durability(item)
    current_damage = item.item_meta.damage if item.item_meta.has_damage else 0
    return max(0, max_dur - current_damage)


def _get_enchant_level(item: ItemStack, enchant_id: str) -> int:
    """Get enchantment level by string ID. Returns 0 if not present."""
    try:
        meta = item.item_meta
        enchants = meta.enchants
        # enchants is dict[Enchantment, int] - need to check by id
        for ench, level in enchants.items():
            if hasattr(ench, 'id') and ench.id == enchant_id:
                return level
            # Fallback: compare string representation
            if str(ench).lower() == enchant_id.lower():
                return level
        return 0
    except Exception:
        return 0


def has_silk_touch(item: ItemStack) -> bool:
    """Check if tool has Silk Touch."""
    return _get_enchant_level(item, ENCHANT_SILK_TOUCH) > 0


def get_fortune_level(item: ItemStack) -> int:
    """Get Fortune enchantment level (0 if not present)."""
    return _get_enchant_level(item, ENCHANT_FORTUNE)


def get_efficiency_level(item: ItemStack) -> int:
    """Get Efficiency level for speed calculation."""
    return _get_enchant_level(item, ENCHANT_EFFICIENCY)


def get_unbreaking_level(item: ItemStack) -> int:
    """Get Unbreaking level for durability calculation."""
    return _get_enchant_level(item, ENCHANT_UNBREAKING)


def should_lose_durability(unbreaking_level: int) -> bool:
    """Calculate if durability should be lost (Unbreaking chance).
    
    Unbreaking gives a (100 / (level + 1))% chance to lose durability.
    """
    if unbreaking_level <= 0:
        return True
    chance = 100.0 / (unbreaking_level + 1)
    return random.random() * 100 < chance


def apply_durability_damage(item: ItemStack, amount: int = 1) -> bool:
    """Apply durability damage to item. Returns True if tool broke."""
    meta = item.item_meta
    current = meta.damage if meta.has_damage else 0
    new_damage = current + amount
    
    max_dur = get_max_durability(item)
    
    if new_damage >= max_dur:
        return True  # Tool broke
    
    meta.damage = new_damage
    item.set_item_meta(meta)
    return False


def is_unbreakable(item: ItemStack) -> bool:
    """Check if tool is unbreakable."""
    return item.item_meta.is_unbreakable
