"""Block drop definitions with Silk Touch and Fortune support."""
import random

# Block -> (normal_drop, silk_drop, fortune_data)
# fortune_data: (base_amount, max_extra_per_fortune_level) or None
BLOCK_DROPS: dict[str, tuple[str, str, tuple[int, int] | None]] = {
    # Standard blocks
    "stone": ("cobblestone", "stone", None),
    "cobblestone": ("cobblestone", "cobblestone", None),
    "deepslate": ("cobbled_deepslate", "deepslate", None),
    "cobbled_deepslate": ("cobbled_deepslate", "cobbled_deepslate", None),
    "netherrack": ("netherrack", "netherrack", None),
    "end_stone": ("end_stone", "end_stone", None),
    "granite": ("granite", "granite", None),
    "diorite": ("diorite", "diorite", None),
    "andesite": ("andesite", "andesite", None),
    "tuff": ("tuff", "tuff", None),
    "calcite": ("calcite", "calcite", None),
    "blackstone": ("blackstone", "blackstone", None),
    "basalt": ("basalt", "basalt", None),
    "obsidian": ("obsidian", "obsidian", None),
    "crying_obsidian": ("crying_obsidian", "crying_obsidian", None),
    
    # Ores - Fortune applies
    "coal_ore": ("coal", "coal_ore", (1, 1)),
    "deepslate_coal_ore": ("coal", "deepslate_coal_ore", (1, 1)),
    "iron_ore": ("raw_iron", "iron_ore", None),
    "deepslate_iron_ore": ("raw_iron", "deepslate_iron_ore", None),
    "gold_ore": ("raw_gold", "gold_ore", None),
    "deepslate_gold_ore": ("raw_gold", "deepslate_gold_ore", None),
    "copper_ore": ("raw_copper", "copper_ore", (2, 1)),
    "deepslate_copper_ore": ("raw_copper", "deepslate_copper_ore", (2, 1)),
    "diamond_ore": ("diamond", "diamond_ore", (1, 1)),
    "deepslate_diamond_ore": ("diamond", "deepslate_diamond_ore", (1, 1)),
    "emerald_ore": ("emerald", "emerald_ore", (1, 1)),
    "deepslate_emerald_ore": ("emerald", "deepslate_emerald_ore", (1, 1)),
    "lapis_ore": ("lapis_lazuli", "lapis_ore", (4, 4)),
    "deepslate_lapis_ore": ("lapis_lazuli", "deepslate_lapis_ore", (4, 4)),
    "redstone_ore": ("redstone", "redstone_ore", (4, 1)),
    "deepslate_redstone_ore": ("redstone", "deepslate_redstone_ore", (4, 1)),
    "nether_quartz_ore": ("quartz", "nether_quartz_ore", (1, 1)),
    "nether_gold_ore": ("gold_nugget", "nether_gold_ore", (2, 3)),
    "ancient_debris": ("ancient_debris", "ancient_debris", None),
    
    # Amethyst
    "amethyst_cluster": ("amethyst_shard", "amethyst_cluster", (4, 0)),
    
    # Glowstone (special Fortune behavior)
    "glowstone": ("glowstone_dust", "glowstone", (2, 1)),
    
    # Gravel - drops itself (flint is handled separately in vanilla)
    "gravel": ("gravel", "gravel", None),
    "sand": ("sand", "sand", None),
    "red_sand": ("red_sand", "red_sand", None),
    "dirt": ("dirt", "dirt", None),
    "grass_block": ("dirt", "grass_block", None),
    "clay": ("clay_ball", "clay", (4, 0)),
}


def normalize_block_type(block_type: str) -> str:
    """Strip namespace from block type."""
    return block_type.lower().replace("minecraft:", "")


def get_drops(block_type: str, silk_touch: bool, fortune_level: int) -> list[tuple[str, int]]:
    """Get drops for a block. Returns list of (item_type, amount)."""
    block_type = normalize_block_type(block_type)
    
    if block_type not in BLOCK_DROPS:
        # Unknown block - drop itself
        return [(f"minecraft:{block_type}", 1)]
    
    normal_drop, silk_drop, fortune_data = BLOCK_DROPS[block_type]
    
    if silk_touch:
        return [(f"minecraft:{silk_drop}", 1)]
    
    amount = 1
    if fortune_data:
        base, per_level = fortune_data
        extra = random.randint(0, per_level * fortune_level) if fortune_level > 0 else 0
        amount = base + extra
    
    return [(f"minecraft:{normal_drop}", amount)]
