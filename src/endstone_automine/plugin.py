"""Auto-Mine Plugin for Endstone.

Allows tagged players to define a mining area and automatically mine blocks
using their equipped pickaxe, respecting enchantments and durability.
Also handles auto-eating and auto-defense against hostile mobs.
"""
import math
from endstone.plugin import Plugin
from endstone import Player
from endstone.level import Location
from endstone.inventory import ItemStack
from endstone.command import Command, CommandSender

from endstone_automine.mining_session import MiningSession
from endstone_automine.tool_utils import (
    is_pickaxe,
    get_remaining_durability,
    has_silk_touch,
    get_fortune_level,
    get_efficiency_level,
    get_unbreaking_level,
    should_lose_durability,
    apply_durability_damage,
    is_unbreakable,
)
from endstone_automine.loot_tables import get_drops
from endstone_automine.combat_utils import (
    is_sword,
    get_sword_damage,
    find_sword_in_inventory,
)
from endstone_automine.food_utils import (
    find_food_in_inventory,
    consume_food,
    get_food_value,
)

# Required player tag to use automine
REQUIRED_TAG = "automine"

# Blocks that cannot be mined
SKIP_BLOCKS = {"minecraft:air", "minecraft:bedrock", "minecraft:barrier"}

# Hazardous blocks - don't teleport player into these
HAZARD_BLOCKS = {
    "minecraft:lava", "minecraft:flowing_lava",
    "minecraft:water", "minecraft:flowing_water",
}

# Hostile mobs to auto-attack (NOT players)
HOSTILE_MOBS = {
    "minecraft:zombie", "minecraft:skeleton", "minecraft:spider",
    "minecraft:creeper", "minecraft:witch", "minecraft:drowned",
    "minecraft:husk", "minecraft:stray", "minecraft:cave_spider",
    "minecraft:pillager", "minecraft:vindicator", "minecraft:evoker",
    "minecraft:phantom", "minecraft:warden", "minecraft:blaze",
    "minecraft:zombie_villager", "minecraft:silverfish", "minecraft:endermite",
    "minecraft:wither_skeleton", "minecraft:guardian", "minecraft:elder_guardian",
    "minecraft:shulker", "minecraft:vex", "minecraft:ravager",
    "minecraft:hoglin", "minecraft:zoglin", "minecraft:piglin_brute",
}

# Health threshold to trigger auto-eat (half-hearts)
HEAL_THRESHOLD = 14  # 7 hearts

# Attack range for auto-defense (blocks)
ATTACK_RANGE = 4.0


class AutoMinePlugin(Plugin):
    """Main plugin class for auto-mining functionality."""
    
    name = "auto_mine"
    api_version = "0.11"
    
    commands = {
        "automine": {
            "description": "Auto-mine an area using your pickaxe",
            "usages": [
                "/automine <x1: int> <y1: int> <z1: int> <x2: int> <y2: int> <z2: int>",
                "/automine stop",
                "/automine status",
            ],
        }
    }
    
    def __init__(self):
        super().__init__()
        self.sessions: dict[str, MiningSession] = {}
        self.tasks: dict = {}  # player_name -> Task object
    
    def on_enable(self) -> None:
        self.logger.info("AutoMine plugin enabled")
    
    def on_disable(self) -> None:
        # Stop all active mining sessions
        for player_name in list(self.sessions.keys()):
            self._stop_mining(player_name, "Plugin disabled")
        self.logger.info("AutoMine plugin disabled")
    
    def on_command(self, sender: CommandSender, command: Command, args: list[str]) -> bool:
        if command.name != "automine":
            return False
        
        if not isinstance(sender, Player):
            sender.send_message("§cThis command can only be used by players.")
            return True
        
        player: Player = sender
        
        # Check for required tag
        if REQUIRED_TAG not in player.scoreboard_tags:
            player.send_message(f"§cYou need the '{REQUIRED_TAG}' tag to use this command.")
            return True
        
        if not args:
            self._send_usage(player)
            return True
        
        subcommand = args[0].lower()
        
        if subcommand == "stop":
            return self._handle_stop(player)
        elif subcommand == "status":
            return self._handle_status(player)
        else:
            # Try to parse as coordinates
            return self._handle_start(player, args)
    
    def _send_usage(self, player: Player) -> None:
        """Send command usage to player."""
        player.send_message("§6=== AutoMine Commands ===")
        player.send_message("§e/automine <x1> <y1> <z1> <x2> <y2> <z2>§7 - Start mining area")
        player.send_message("§e/automine stop§7 - Stop mining")
        player.send_message("§e/automine status§7 - Check progress")
    
    def _handle_stop(self, player: Player) -> bool:
        """Handle /automine stop command."""
        if player.name not in self.sessions:
            player.send_message("§cYou don't have an active mining session.")
            return True
        
        self._stop_mining(player.name, "§eMining stopped by player.")
        return True
    
    def _handle_status(self, player: Player) -> bool:
        """Handle /automine status command."""
        session = self.sessions.get(player.name)
        if not session:
            player.send_message("§cNo active mining session.")
            return True
        
        player.send_message(f"§6=== Mining Status ===")
        player.send_message(f"§eBlocks mined:§f {session.blocks_mined}/{session.total_blocks()}")
        player.send_message(f"§eProgress:§f {session.progress_percent():.1f}%")
        player.send_message(f"§eCurrent layer:§f Y={session.current_y}")
        
        # Show pickaxe durability
        held = player.inventory.item_in_main_hand
        if is_pickaxe(held):
            remaining = get_remaining_durability(held)
            player.send_message(f"§eDurability:§f {remaining}")
        
        return True
    
    def _handle_start(self, player: Player, args: list[str]) -> bool:
        """Handle /automine <coords> command to start mining."""
        # Need exactly 6 coordinate values
        if len(args) != 6:
            player.send_message("§cUsage: /automine <x1> <y1> <z1> <x2> <y2> <z2>")
            return True
        
        # Parse coordinates
        try:
            x1, y1, z1, x2, y2, z2 = [int(a) for a in args]
        except ValueError:
            player.send_message("§cAll coordinates must be integers.")
            return True
        
        # Check for existing session
        if player.name in self.sessions:
            player.send_message("§cYou already have an active mining session. Use §e/automine stop§c first.")
            return True
        
        # Check for pickaxe in hand
        held_item = player.inventory.item_in_main_hand
        if not is_pickaxe(held_item):
            player.send_message("§cYou must hold a pickaxe to start mining!")
            return True
        
        # Check durability
        remaining = get_remaining_durability(held_item)
        if remaining <= 0:
            player.send_message("§cYour pickaxe is broken!")
            return True
        
        # Normalize bounds
        min_x, max_x = min(x1, x2), max(x1, x2)
        min_y, max_y = min(y1, y2), max(y1, y2)
        min_z, max_z = min(z1, z2), max(z1, z2)
        
        # Get dimension name
        dim_name = self._normalize_dimension(player.dimension)
        
        # Get player's current position to return to later
        player_loc = player.location
        
        # Create session
        session = MiningSession(
            player_name=player.name,
            dimension_name=dim_name,
            min_x=min_x, max_x=max_x,
            min_y=min_y, max_y=max_y,
            min_z=min_z, max_z=max_z,
            start_x=player_loc.x,
            start_y=player_loc.y,
            start_z=player_loc.z,
        )
        self.sessions[player.name] = session
        
        # Calculate mining delay based on efficiency
        delay = self._get_mining_delay(held_item)
        
        # Store player name in closure
        player_name = player.name
        
        # Start mining loop
        def mining_tick():
            self._process_mining_tick(player_name)
        
        task = self.server.scheduler.run_task(self, mining_tick, delay=10, period=delay)
        self.tasks[player.name] = task
        
        total = session.total_blocks()
        player.send_message(f"§aStarted mining! Area: {total} blocks")
        player.send_message(f"§7Mining from ({min_x}, {min_y}, {min_z}) to ({max_x}, {max_y}, {max_z})")
        
        return True
    
    def _normalize_dimension(self, dimension) -> str:
        """Normalize dimension object to string name."""
        name = getattr(dimension, 'name', str(dimension)).lower()
        if 'name=' in name:
            name = name.split("name='")[-1].split("'")[0]
        if ":" in name:
            name = name.split(":")[-1]
        return name.strip()
    
    def _get_mining_delay(self, item: ItemStack) -> int:
        """Calculate ticks between blocks based on Efficiency."""
        base_delay = 15  # 0.75 seconds
        eff_level = get_efficiency_level(item)
        # Each efficiency level reduces delay by 2 ticks, minimum 4 ticks
        return max(4, base_delay - (eff_level * 2))
    
    def _get_player(self, name: str) -> Player | None:
        """Get online player by name."""
        for player in self.server.online_players:
            if player.name == name:
                return player
        return None
    
    def _stop_mining(self, player_name: str, message: str = None) -> None:
        """Stop a mining session and clean up."""
        # Get session before removing it (need start position)
        session = self.sessions.get(player_name)
        
        # Cancel scheduled task
        if player_name in self.tasks:
            task = self.tasks.pop(player_name)
            try:
                task.cancel()
            except Exception:
                pass  # Task may already be cancelled
        
        # Remove session
        self.sessions.pop(player_name, None)
        
        # Return player to starting position and notify
        player = self._get_player(player_name)
        if player:
            if session:
                # Teleport back to start position
                player.teleport(Location(
                    player.dimension, 
                    session.start_x, 
                    session.start_y, 
                    session.start_z
                ))
            if message:
                player.send_message(message)
    
    def _process_mining_tick(self, player_name: str) -> None:
        """Process one mining tick for a player."""
        try:
            self._do_mining_tick(player_name)
        except Exception as e:
            self.logger.error(f"Mining tick error for {player_name}: {e}")
            self._stop_mining(player_name, f"§cMining error: {e}")
    
    def _do_mining_tick(self, player_name: str) -> None:
        """Actual mining tick logic."""
        session = self.sessions.get(player_name)
        if not session or not session.is_active:
            self._stop_mining(player_name)
            return
        
        # Get player
        player = self._get_player(player_name)
        if not player:
            self._stop_mining(player_name, "Player disconnected")
            return
        
        # Check pickaxe
        held_item = player.inventory.item_in_main_hand
        if not is_pickaxe(held_item):
            self._stop_mining(player_name, "§cNo pickaxe in hand! Mining stopped.")
            return
        
        # Check durability
        if not is_unbreakable(held_item):
            remaining = get_remaining_durability(held_item)
            if remaining <= 0:
                self._stop_mining(player_name, "§cPickaxe broke! Mining stopped.")
                return
        
        # Get current position
        pos = session.get_current_position()
        if pos is None:
            self._stop_mining(player_name, "§aMining complete!")
            return
        
        x, y, z = pos
        dim = player.dimension
        
        # Get block at position
        block = dim.get_block_at(x, y, z)
        block_type = block.type
        
        # Skip air, bedrock, etc.
        if block_type in SKIP_BLOCKS:
            player.send_tip(f"§7Skip: air/bedrock §8| §e{session.blocks_mined}/{session.total_blocks()} §8| §b({x}, {y}, {z})")
            session.advance()
            return
        
        # Skip hazardous blocks (lava/water) - don't teleport into danger
        if block_type in HAZARD_BLOCKS:
            player.send_tip(f"§6Skip: hazard §8| §e{session.blocks_mined}/{session.total_blocks()} §8| §b({x}, {y}, {z})")
            session.advance()
            return
        
        # Check if destination is safe - check all 6 adjacent blocks for liquids
        # If breaking this block would cause lava/water to flow in, skip it
        adjacent_offsets = [
            (0, 1, 0),   # above
            (0, -1, 0),  # below
            (1, 0, 0),   # east
            (-1, 0, 0),  # west
            (0, 0, 1),   # south
            (0, 0, -1),  # north
        ]
        
        has_adjacent_hazard = False
        for dx, dy, dz in adjacent_offsets:
            adj_block = dim.get_block_at(x + dx, y + dy, z + dz)
            if adj_block.type in HAZARD_BLOCKS:
                has_adjacent_hazard = True
                break
        
        if has_adjacent_hazard:
            player.send_tip(f"§6Skip: liquid nearby §8| §e{session.blocks_mined}/{session.total_blocks()} §8| §b({x}, {y}, {z})")
            session.advance()
            return
        
        # Teleport player to position (standing on block)
        player.teleport(Location(dim, x + 0.5, y + 1.0, z + 0.5))
        
        # Calculate drops based on enchantments
        silk = has_silk_touch(held_item)
        fortune = get_fortune_level(held_item)
        drops = get_drops(block_type, silk, fortune)
        
        # Break the block
        block.set_type("minecraft:air")
        
        # Spawn drops - give directly to player via command
        for item_type, amount in drops:
            if amount > 0:
                # Use give command (silent)
                cmd = f"give {player.name} {item_type} {amount}"
                self.server.dispatch_command(self.server.command_sender, cmd)
        
        # Apply durability damage (unless unbreakable)
        if not is_unbreakable(held_item):
            unbreaking = get_unbreaking_level(held_item)
            if should_lose_durability(unbreaking):
                if apply_durability_damage(held_item):
                    # Tool broke
                    player.inventory.item_in_main_hand = ItemStack("minecraft:air", 0)
                    self._stop_mining(player_name, "§cPickaxe broke! Mining stopped.")
                    return
                # Update the item in hand
                player.inventory.item_in_main_hand = held_item
        
        session.blocks_mined += 1
        session.advance()
        
        # Auto-eat and auto-defense checks
        self._check_auto_eat(player)
        self._check_auto_defense(player)
        
        # Show actionbar feedback every tick
        remaining_dur = get_remaining_durability(held_item) if not is_unbreakable(held_item) else "∞"
        short_type = block_type.split(":")[-1] if ":" in block_type else block_type
        player.send_tip(
            f"§aMined: {short_type} §8| §e{session.blocks_mined}/{session.total_blocks()} "
            f"§8| §7Dur: {remaining_dur} §8| §b({x},{y},{z})"
        )
    
    def _check_auto_eat(self, player: Player) -> None:
        """Check if player needs food and auto-eat from inventory."""
        try:
            # Check health (Mob.health property)
            if player.health >= HEAL_THRESHOLD:
                return  # Health is fine
            
            # Find food in inventory
            food_result = find_food_in_inventory(player)
            if not food_result:
                return  # No food available
            
            slot, food_item = food_result
            food_value = get_food_value(food_item)
            
            # Consume food from inventory
            if consume_food(player, slot):
                # Apply saturation effect to restore hunger/health
                cmd = f"effect {player.name} saturation 2 {min(food_value // 2, 5)} true"
                self.server.dispatch_command(self.server.command_sender, cmd)
        except Exception:
            pass  # Ignore errors in auto-eat
    
    def _check_auto_defense(self, player: Player) -> None:
        """Check for nearby hostile mobs and attack them."""
        try:
            dim = player.dimension
            player_loc = player.location
            px, py, pz = player_loc.x, player_loc.y, player_loc.z
            
            # Find sword in inventory
            sword_result = find_sword_in_inventory(player)
            sword_damage = 1  # Fist damage
            if sword_result:
                _, sword = sword_result
                sword_damage = get_sword_damage(sword)
            
            # Check all actors in dimension
            for actor in dim.actors:
                # Skip non-hostile mobs (and players!)
                if actor.type not in HOSTILE_MOBS:
                    continue
                
                # Skip dead actors
                if actor.is_dead:
                    continue
                
                # Calculate distance
                actor_loc = actor.location
                ax, ay, az = actor_loc.x, actor_loc.y, actor_loc.z
                distance = math.sqrt((ax - px)**2 + (ay - py)**2 + (az - pz)**2)
                
                if distance <= ATTACK_RANGE:
                    # Attack the mob using damage command
                    cmd = f"damage @e[type={actor.type},c=1,r=5] {sword_damage} entity_attack entity {player.name}"
                    self.server.dispatch_command(self.server.command_sender, cmd)
                    break  # Only attack one mob per tick
        except Exception:
            pass  # Ignore errors in auto-defense
