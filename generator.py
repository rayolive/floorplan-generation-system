import matplotlib.pyplot as plt
import random
import copy # Added for deep copying

# ------------------ Data Models ------------------ #
class Room:
    def __init__(self, width, height, name):
        self.width = width
        self.height = height
        self.name = name
        self.x = 0
        self.y = 0
        
        # Store original dimensions for resetting after rotation
        self._original_width = width
        self._original_height = height

    def area(self):
        return self.width * self.height
        
    def rotate(self):
        """Swaps width and height."""
        self.width, self.height = self.height, self.width
        
    def reset_rotation(self):
        """Resets width and height to their original values."""
        self.width = self._original_width
        self.height = self._original_height


class Plot:
    def __init__(self, width, height):
        self.width = width
        self.height = height

    def area(self):
        return self.width * self.height


# ------------------ Collision Detection Helpers (NEW) ------------------ #

def overlaps(r1, r2):
    """Checks if two rooms (rectangles) overlap."""
    # Check if r1 is to the right of r2
    if r1.x >= r2.x + r2.width:
        return False
    # Check if r1 is to the left of r2
    if r1.x + r1.width <= r2.x:
        return False
    # Check if r1 is above r2
    if r1.y >= r2.y + r2.height:
        return False
    # Check if r1 is below r2
    if r1.y + r1.height <= r2.y:
        return False
    # If none of the above, they must overlap
    return True

def out_of_bounds(room, plot):
    """Checks if a room is outside the plot boundaries."""
    if room.x < 0 or room.y < 0:
        return True
    if room.x + room.width > plot.width:
        return True
    if room.y + room.height > plot.height:
        return True
    return False

def check_collision(new_room, placed_rooms, plot):
    """
    Checks if a new room collides with the plot boundary
    or any already placed room.
    """
    # Check plot boundaries
    if out_of_bounds(new_room, plot):
        return True
        
    # Check against all other placed rooms
    for p_room in placed_rooms:
        if overlaps(new_room, p_room):
            return True
            
    # No collisions
    return False


# ------------------ Core Algorithm (REVISED) ------------------ #

def try_place_room(room, test_x, test_y, placed, plot):
    """Helper to test a room at a location, with rotation."""
    
    # 1. Try placing without rotation
    room.reset_rotation()
    if random.choice([True, False]): # 50% chance to try rotation first
        room.rotate()
        
    room.x, room.y = test_x, test_y
    if not check_collision(room, placed, plot):
        return True # Placed successfully

    # 2. Try placing with rotation (if first try failed)
    room.rotate() # Flip to the other orientation
    room.x, room.y = test_x, test_y
    if not check_collision(room, placed, plot):
        return True # Placed successfully
        
    # 3. Failed to place
    room.reset_rotation() # Reset for next attempt
    return False


def boundary_pack_revised(rooms, plot, corridor_width=3, corridor_prob=0.3, seed=None):
    """
    Tries to arrange rooms along the boundary with collision checks
    and probabilistic corridors.
    """
    if seed is not None:
        random.seed(seed)
        
    # Make a deep copy to avoid modifying original list and rooms
    rooms_to_place = copy.deepcopy(rooms)
    random.shuffle(rooms_to_place)
    
    placed = []
    
    # --- 1. Place along bottom edge (Left to Right) ---
    current_x = 0
    max_h_bottom = 0 # Track max height in this row to avoid simple overlaps
    for room in rooms_to_place:
        if room in placed:
            continue
            
        gap = corridor_width if random.random() < corridor_prob else 0
        test_x = current_x + gap
        test_y = 0 # Place flush at the bottom
        
        if try_place_room(room, test_x, 0, placed, plot):
            placed.append(room)
            current_x = room.x + room.width
            max_h_bottom = max(max_h_bottom, room.height)
        
    # --- 2. Place along right edge (Bottom to Top) ---
    current_y = 0
    max_w_right = 0
    for room in rooms_to_place:
        if room in placed:
            continue
            
        gap = corridor_width if random.random() < corridor_prob else 0
        test_y = current_y + gap
        
        # We must test both rotations, as x depends on width
        
        # Try initial orientation
        room.reset_rotation()
        if random.choice([True, False]):
             room.rotate()
        test_x = plot.width - room.width
        room.x, room.y = test_x, test_y
        
        if not check_collision(room, placed, plot):
            placed.append(room)
            current_y = room.y + room.height
            max_w_right = max(max_w_right, room.width)
            continue
            
        # Try other orientation
        room.rotate()
        test_x = plot.width - room.width
        room.x, room.y = test_x, test_y
        
        if not check_collision(room, placed, plot):
            placed.append(room)
            current_y = room.y + room.height
            max_w_right = max(max_w_right, room.width)

    # --- 3. Place along top edge (Right to Left) ---
    current_x = plot.width
    for room in rooms_to_place:
        if room in placed:
            continue
            
        gap = corridor_width if random.random() < corridor_prob else 0
        
        # Try initial orientation
        room.reset_rotation()
        if random.choice([True, False]):
             room.rotate()
        test_x = current_x - room.width - gap
        test_y = plot.height - room.height
        room.x, room.y = test_x, test_y
        
        if not check_collision(room, placed, plot):
            placed.append(room)
            current_x = room.x
            continue

        # Try other orientation
        room.rotate()
        test_x = current_x - room.width - gap
        test_y = plot.height - room.height
        room.x, room.y = test_x, test_y
        
        if not check_collision(room, placed, plot):
            placed.append(room)
            current_x = room.x
            
    # --- 4. Place along left edge (Top to Bottom) ---
    current_y = plot.height
    for room in rooms_to_place:
        if room in placed:
            continue
            
        gap = corridor_width if random.random() < corridor_prob else 0
        
        # Try initial orientation
        room.reset_rotation()
        if random.choice([True, False]):
             room.rotate()
        test_x = 0
        test_y = current_y - room.height - gap
        room.x, room.y = test_x, test_y
        
        if not check_collision(room, placed, plot):
            placed.append(room)
            current_y = room.y
            continue

        # Try other orientation
        room.rotate()
        test_x = 0
        test_y = current_y - room.height - gap
        room.x, room.y = test_x, test_y
        
        if not check_collision(room, placed, plot):
            placed.append(room)
            current_y = room.y

    # --- 5. Report unplaced rooms ---
    # The random "inner" placement from your original code is
    # removed as it guarantees overlaps.
    unplaced = [r for r in rooms if r not in placed]
    
    return placed, unplaced


# ------------------ Visualization (REVISED) ------------------ #
def visualize_layout(placed, unplaced, plot, layout_no):
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.set_xlim(0, plot.width)
    ax.set_ylim(0, plot.height)
    ax.set_aspect('equal')
    
    unplaced_names = ", ".join([r.name for r in unplaced])
    if not unplaced_names:
        unplaced_names = "None"
    ax.set_title(f"Layout {layout_no} | Unplaced: {unplaced_names}")

    # Draw plot boundary
    ax.add_patch(plt.Rectangle((0, 0), plot.width, plot.height, fill=False, edgecolor='black', linewidth=2))
    
    # --- NEW: Show circulation as the background ---
    # The "remaining area" is the circulation
    ax.add_patch(plt.Rectangle((0, 0), plot.width, plot.height, facecolor='lightgray', label='Circulation'))
    
    # Draw placed rooms
    for r in placed:
        rect = plt.Rectangle((r.x, r.y), r.width, r.height,
                             facecolor=random.choice(['#a8e6cf', '#dcedc1', '#ffd3b6', '#ffaaa5', '#ff8b94']),
                             edgecolor='black', alpha=0.9,
                             linewidth=1.5)
        ax.add_patch(rect)
        ax.text(r.x + r.width/2, r.y + r.height/2, f"{r.name}\n{r.width}x{r.height}",
                ha='center', va='center', fontsize=8, weight='bold')

    plt.show()


# ------------------ Runner ------------------ #
def main():
    plot = Plot(25, 11) # Made plot bigger for better packing
    rooms = [
        Room(6, 4, "R1"),
        Room(5, 5, "R2"),
        Room(3, 6, "R3"),
        Room(4, 4, "R4"),
        Room(8, 4, "R5"),
        Room(3, 5, "R6"),
        Room(7, 3, "R7"),
        Room(5, 5, "R8"),
    ]

    total_area = sum(r.area() for r in rooms)
    plot_area = plot.area()
    
    print(f"Plot Area: {plot_area}")
    print(f"Total Room Area: {total_area}")
    print(f"Room Area Percentage: {100 * total_area / plot_area:.2f}%")
    
    if total_area > 0.7 * plot_area:
        print("❌ Infeasible layout: total room area exceeds 70% of plot.")
        return

    # Generate 3 random layouts
    for i in range(3):
        placed, unplaced = boundary_pack_revised(rooms, plot, 
                                                 corridor_width=3, 
                                                 corridor_prob=0.3, 
                                                 seed=i)
        
        print(f"\n--- Layout {i+1} (Seed={i}) ---")
        print(f"Placed Rooms: {len(placed)}")
        for r in placed:
            print(f"  {r.name}: ({r.x:.1f}, {r.y:.1f}) -> {r.width}x{r.height}")
        
        print(f"Unplaced Rooms: {len(unplaced)}")
        for r in unplaced:
            print(f"  {r.name} ({r.width}x{r.height}) could not be placed.")
            
        visualize_layout(placed, unplaced, plot, i+1)


if __name__ == "__main__":
    main()