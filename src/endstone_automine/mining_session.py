"""Mining session state management."""
from dataclasses import dataclass, field


@dataclass
class MiningSession:
    """Tracks the state and progress of a mining operation."""
    player_name: str
    dimension_name: str
    
    # Bounds (normalized so min <= max)
    min_x: int
    max_x: int
    min_y: int
    max_y: int
    min_z: int
    max_z: int
    
    # Player's starting position (to return to when done)
    start_x: float = 0.0
    start_y: float = 0.0
    start_z: float = 0.0
    
    # Current position in mining pattern
    current_x: int = field(init=False)
    current_y: int = field(init=False)
    current_z: int = field(init=False)
    
    # Progress tracking
    blocks_mined: int = 0
    is_active: bool = True
    
    def __post_init__(self):
        """Initialize starting position at top layer."""
        # Start mining from top-down, sweep in X then Z
        self.current_x = self.min_x
        self.current_y = self.max_y  # Start at top
        self.current_z = self.min_z
    
    def get_current_position(self) -> tuple[int, int, int] | None:
        """Get current block position to mine, or None if complete."""
        if not self.is_active:
            return None
        if self.current_y < self.min_y:
            return None  # Finished all layers
        return (self.current_x, self.current_y, self.current_z)
    
    def advance(self) -> bool:
        """Move to next position. Returns False if mining complete."""
        # Advance X
        self.current_x += 1
        if self.current_x > self.max_x:
            self.current_x = self.min_x
            # Advance Z
            self.current_z += 1
            if self.current_z > self.max_z:
                self.current_z = self.min_z
                # Advance Y (go down one layer)
                self.current_y -= 1
                if self.current_y < self.min_y:
                    self.is_active = False
                    return False
        return True
    
    def total_blocks(self) -> int:
        """Calculate total blocks in the mining area."""
        return ((self.max_x - self.min_x + 1) *
                (self.max_y - self.min_y + 1) *
                (self.max_z - self.min_z + 1))
    
    def progress_percent(self) -> float:
        """Get current progress as percentage."""
        total = self.total_blocks()
        if total == 0:
            return 100.0
        return (self.blocks_mined / total) * 100
