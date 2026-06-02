import matplotlib.pyplot as plt
import random
import copy
from collections import defaultdict

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


# ------------------ Improved Collision Detection ------------------ #

def overlaps(r1, r2, tolerance=0.0):
    """Checks if two rooms overlap with optional tolerance for small gaps."""
    if r1.x >= r2.x + r2.width + tolerance:
        return False
    if r1.x + r1.width + tolerance <= r2.x:
        return False
    if r1.y >= r2.y + r2.height + tolerance:
        return False
    if r1.y + r1.height + tolerance <= r2.y:
        return False
    return True

def out_of_bounds(room, plot, tolerance=0.0):
    """Checks if a room is outside the plot boundaries with tolerance."""
    if room.x < -tolerance or room.y < -tolerance:
        return True
    if room.x + room.width > plot.width + tolerance:
        return True
    if room.y + room.height > plot.height + tolerance:
        return True
    return False

def check_collision(new_room, placed_rooms, plot, overlap_tolerance=0.0, bounds_tolerance=0.0):
    """Checks collision with configurable tolerances."""
    if out_of_bounds(new_room, plot, bounds_tolerance):
        return True
    for p_room in placed_rooms:
        if overlaps(new_room, p_room, -overlap_tolerance):  # Negative for allowing small overlaps
            return True
    return False


# ------------------ Scoring System ------------------ #

def calculate_layout_score(placed, plot, corridor_width):
    """
    Calculate a comprehensive score for the layout.
    Higher score = better layout.
    
    Enhanced scoring priorities:
    1. Place all rooms (10,000 pts per room)
    2. All rooms must be corridor-connected (-5,000 pts per disconnected room)
    3. Direct room-to-room connectivity via single corridor edge (500 pts per pair)
    4. Corridor quality and consistency (up to 5,000 pts)
    5. Minimize choke points (up to 2,000 pts)
    6. Space utilization ~70% (up to 1,000 pts)
    7. Layout regularity and organization (up to 1,500 pts)
    """
    if not placed:
        return 0
    
    score = 0
    from collections import defaultdict, deque
    
    # ========== PRIORITY 1: PLACE ALL ROOMS (10,000 pts per room) ==========
    score += len(placed) * 10000
    
    # ========== BUILD CORRIDOR NETWORK ==========
    # Build adjacency graph of rooms connected by corridors
    adjacency = defaultdict(set)
    corridor_segments = []
    direct_connections = 0  # Count of direct room-to-room connections
    
    for i, r1 in enumerate(placed):
        for r2 in placed[i+1:]:
            is_connected = False
            connection_quality = 0
            
            # HORIZONTAL CORRIDORS: Rooms side-by-side (separated left-right)
            if abs(r1.y - r2.y) < 0.5 or abs((r1.y + r1.height) - (r2.y + r2.height)) < 0.5:
                gap = abs(r1.x + r1.width - r2.x) if r1.x < r2.x else abs(r2.x + r2.width - r1.x)
                
                if 0 < gap <= corridor_width + 1:
                    is_connected = True
                    corridor_segments.append(('horizontal', gap, r1, r2))
                    
                    # Exact corridor width gets best score
                    if abs(gap - corridor_width) < 0.1:
                        connection_quality = 500
                    # Close to corridor width
                    elif abs(gap - corridor_width) < 0.5:
                        connection_quality = 300
                    # Acceptable but not ideal
                    else:
                        connection_quality = 150
            
            # VERTICAL CORRIDORS: Rooms stacked (separated top-bottom)
            if not is_connected:
                if abs(r1.x - r2.x) < 0.5 or abs((r1.x + r1.width) - (r2.x + r2.width)) < 0.5:
                    gap = abs(r1.y + r1.height - r2.y) if r1.y < r2.y else abs(r2.y + r2.height - r1.y)
                    
                    if 0 < gap <= corridor_width + 1:
                        is_connected = True
                        corridor_segments.append(('vertical', gap, r1, r2))
                        
                        # Exact corridor width gets best score
                        if abs(gap - corridor_width) < 0.1:
                            connection_quality = 500
                        # Close to corridor width
                        elif abs(gap - corridor_width) < 0.5:
                            connection_quality = 300
                        # Acceptable but not ideal
                        else:
                            connection_quality = 150
            
            # If rooms are directly connected via corridor
            if is_connected:
                adjacency[id(r1)].add(id(r2))
                adjacency[id(r2)].add(id(r1))
                score += connection_quality
                direct_connections += 1
    
    # ========== PRIORITY 2: ALL ROOMS MUST BE CONNECTED (-5,000 per disconnected) ==========
    # Check which rooms are connected to the corridor network
    if len(placed) > 1:
        # Find largest connected component using BFS
        visited = set()
        queue = deque([id(placed[0])])
        visited.add(id(placed[0]))
        
        while queue:
            current = queue.popleft()
            for neighbor in adjacency[current]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        
        # Heavily penalize disconnected rooms
        connected_count = len(visited)
        disconnected_count = len(placed) - connected_count
        
        if disconnected_count > 0:
            score -= disconnected_count * 5000  # -5000 per disconnected room
            print(f"WARNING: {disconnected_count} rooms not connected to corridor network!")
        else:
            # Bonus for all rooms connected
            score += 2000
    
    # ========== PRIORITY 3: DIRECT CONNECTIVITY (500 pts per pair within 1 edge) ==========
    # Reward layouts where each room can reach others via single corridor
    # This is already counted above in the adjacency building
    # Additional bonus for high average connectivity
    if len(placed) > 1:
        avg_connections = sum(len(adjacency[id(r)]) for r in placed) / len(placed)
        
        # Reward based on average connectivity
        if avg_connections >= 3.5:
            score += 1500  # Excellent - each room connects to 3-4 others
        elif avg_connections >= 2.5:
            score += 1000  # Good - each room connects to 2-3 others
        elif avg_connections >= 1.5:
            score += 500   # Decent - each room connects to 1-2 others
        elif avg_connections >= 1.0:
            score += 200   # Minimal - at least one connection per room
        else:
            score -= 500   # Poor connectivity
    
    # ========== PRIORITY 4: MINIMIZE CHOKE POINTS (up to 2,000 pts) ==========
    for room in placed:
        accessible_directions = 0
        
        # Check each direction for corridor-width access
        # Right
        right_clear = True
        for other in placed:
            if other != room and other.x > room.x + room.width:
                gap = other.x - (room.x + room.width)
                if gap < corridor_width and abs(other.y - room.y) < room.height:
                    right_clear = False
                    break
        if right_clear or room.x + room.width >= plot.width - 0.5:
            accessible_directions += 1
        
        # Left
        left_clear = True
        for other in placed:
            if other != room and other.x + other.width < room.x:
                gap = room.x - (other.x + other.width)
                if gap < corridor_width and abs(other.y - room.y) < room.height:
                    left_clear = False
                    break
        if left_clear or room.x <= 0.5:
            accessible_directions += 1
        
        # Top
        top_clear = True
        for other in placed:
            if other != room and other.y > room.y + room.height:
                gap = other.y - (room.y + room.height)
                if gap < corridor_width and abs(other.x - room.x) < room.width:
                    top_clear = False
                    break
        if top_clear or room.y + room.height >= plot.height - 0.5:
            accessible_directions += 1
        
        # Bottom
        bottom_clear = True
        for other in placed:
            if other != room and other.y + other.height < room.y:
                gap = room.y - (other.y + other.height)
                if gap < corridor_width and abs(other.x - room.x) < room.width:
                    bottom_clear = False
                    break
        if bottom_clear or room.y <= 0.5:
            accessible_directions += 1
        
        # Award/penalize based on accessibility
        if accessible_directions >= 3:
            score += 250  # Excellent accessibility
        elif accessible_directions == 2:
            score += 150  # Good - typical corridor room
        elif accessible_directions == 1:
            score -= 200  # Dead end - penalize more heavily
        else:
            score -= 500  # Trapped room - severe penalty
    
    # ========== PRIORITY 5: SPACE UTILIZATION ~70% (up to 1,000 pts) ==========
    total_placed_area = sum(r.area() for r in placed)
    plot_area = plot.area()
    utilization = total_placed_area / plot_area if plot_area > 0 else 0
    
    target_utilization = 0.70
    utilization_diff = abs(utilization - target_utilization)
    
    if utilization_diff < 0.05:
        score += 1000
    elif utilization_diff < 0.10:
        score += 600
    elif utilization_diff < 0.15:
        score += 300
    else:
        score -= int(utilization_diff * 400)
    
    # ========== PRIORITY 6: LAYOUT REGULARITY (up to 1,500 pts) ==========
    
    # Grid alignment (organized layout)
    x_coords = set()
    y_coords = set()
    for r in placed:
        x_coords.add(round(r.x, 1))
        x_coords.add(round(r.x + r.width, 1))
        y_coords.add(round(r.y, 1))
        y_coords.add(round(r.y + r.height, 1))
    
    # Fewer unique coordinates = more regular grid
    coord_regularity = 1.0 / (len(x_coords) + len(y_coords)) * 2000
    score += min(coord_regularity * 500, 800)
    
    # Edge utilization (rooms against boundaries)
    edge_rooms = 0
    for r in placed:
        on_edge = False
        if abs(r.x) < 0.5:
            on_edge = True
        if abs(r.x + r.width - plot.width) < 0.5:
            on_edge = True
        if abs(r.y) < 0.5:
            on_edge = True
        if abs(r.y + r.height - plot.height) < 0.5:
            on_edge = True
        
        if on_edge:
            edge_rooms += 1
            score += 40
    
    # Bonus for using all edges
    if edge_rooms >= len(placed) * 0.6:  # At least 60% on edges
        score += 400
    
    # Corridor consistency bonus (similar corridor widths throughout)
    if corridor_segments:
        corridor_gaps = [gap for _, gap, _, _ in corridor_segments]
        gap_variance = sum((g - corridor_width) ** 2 for g in corridor_gaps) / len(corridor_gaps)
        
        if gap_variance < 0.05:  # Very consistent corridors
            score += 500
        elif gap_variance < 0.15:
            score += 250
    
    return score


# ------------------ Improved Placement Strategy ------------------ #

def find_all_candidate_positions(room, placed, plot, corridor_width, corridor_prob, allow_overlap=False):
    """Find all possible positions for a room with corridor-aware strategies."""
    candidates = []
    tolerance = 0.5 if allow_overlap else 0.0
    bounds_tolerance = 0.2 if allow_overlap else 0.0
    
    # Determine if we should add corridor spacing (probabilistic)
    add_corridor = random.random() < corridor_prob
    spacing = corridor_width if add_corridor else 0
    
    # Strategy 1: Boundary placement with proper corridor tracking
    if not placed:
        # First room - place at origin
        candidates.append((0, 0, 'first', 100))
    else:
        # Find boundary positions that maintain corridors
        # Bottom edge (left to right)
        current_x = 0
        for existing in sorted([r for r in placed if r.y == 0], key=lambda r: r.x):
            # Try to place before this room
            test_x = current_x
            room.x, room.y = test_x, 0
            if test_x + room.width + spacing <= existing.x:
                if not check_collision(room, placed, plot, tolerance, bounds_tolerance):
                    candidates.append((test_x, 0, 'bottom', 50))
            current_x = existing.x + existing.width + spacing
        
        # After last room on bottom edge
        test_x = current_x
        room.x, room.y = test_x, 0
        if test_x + room.width <= plot.width:
            if not check_collision(room, placed, plot, tolerance, bounds_tolerance):
                candidates.append((test_x, 0, 'bottom', 50))
        
        # Right edge (bottom to top)
        current_y = 0
        for existing in sorted([r for r in placed if r.x + r.width >= plot.width - 1], key=lambda r: r.y):
            test_y = current_y
            test_x = plot.width - room.width
            room.x, room.y = test_x, test_y
            if test_y + room.height + spacing <= existing.y:
                if not check_collision(room, placed, plot, tolerance, bounds_tolerance):
                    candidates.append((test_x, test_y, 'right', 50))
            current_y = existing.y + existing.height + spacing
        
        # After last room on right edge
        test_y = current_y
        test_x = plot.width - room.width
        room.x, room.y = test_x, test_y
        if test_y + room.height <= plot.height:
            if not check_collision(room, placed, plot, tolerance, bounds_tolerance):
                candidates.append((test_x, test_y, 'right', 50))
        
        # Top edge (right to left)
        current_x = plot.width
        for existing in sorted([r for r in placed if r.y + r.height >= plot.height - 1], key=lambda r: r.x, reverse=True):
            test_x = current_x - room.width
            test_y = plot.height - room.height
            room.x, room.y = test_x, test_y
            if test_x >= existing.x + existing.width + spacing:
                if not check_collision(room, placed, plot, tolerance, bounds_tolerance):
                    candidates.append((test_x, test_y, 'top', 50))
            current_x = existing.x - spacing
        
        # Before first room on top edge
        test_x = current_x - room.width
        test_y = plot.height - room.height
        room.x, room.y = test_x, test_y
        if test_x >= 0:
            if not check_collision(room, placed, plot, tolerance, bounds_tolerance):
                candidates.append((test_x, test_y, 'top', 50))
        
        # Left edge (top to bottom)
        current_y = plot.height
        for existing in sorted([r for r in placed if r.x == 0], key=lambda r: r.y, reverse=True):
            test_x = 0
            test_y = current_y - room.height
            room.x, room.y = test_x, test_y
            if test_y >= existing.y + existing.height + spacing:
                if not check_collision(room, placed, plot, tolerance, bounds_tolerance):
                    candidates.append((test_x, test_y, 'left', 50))
            current_y = existing.y - spacing
        
        # Before first room on left edge
        test_x = 0
        test_y = current_y - room.height
        room.x, room.y = test_x, test_y
        if test_y >= 0:
            if not check_collision(room, placed, plot, tolerance, bounds_tolerance):
                candidates.append((test_x, test_y, 'left', 50))
    
    # Strategy 2: Place adjacent to existing rooms (maintain corridor structure)
    for existing in placed:
        # Right of existing room
        x, y = existing.x + existing.width + spacing, existing.y
        room.x, room.y = x, y
        if not check_collision(room, placed, plot, tolerance, bounds_tolerance):
            candidates.append((x, y, 'adjacent', 70))  # Higher priority
        
        # Below existing room
        x, y = existing.x, existing.y + existing.height + spacing
        room.x, room.y = x, y
        if not check_collision(room, placed, plot, tolerance, bounds_tolerance):
            candidates.append((x, y, 'adjacent', 70))
        
        # Left of existing room (only if there's space)
        x, y = existing.x - room.width - spacing, existing.y
        if x >= 0:
            room.x, room.y = x, y
            if not check_collision(room, placed, plot, tolerance, bounds_tolerance):
                candidates.append((x, y, 'adjacent', 70))
        
        # Above existing room (only if there's space)
        x, y = existing.x, existing.y - room.height - spacing
        if y >= 0:
            room.x, room.y = x, y
            if not check_collision(room, placed, plot, tolerance, bounds_tolerance):
                candidates.append((x, y, 'adjacent', 70))
    
    # Strategy 3: Fill interior gaps (lower priority, maintains structure)
    if len(candidates) < 10 and len(placed) > 3:
        step = max(2, corridor_width)  # Use corridor width as step
        for x in range(0, plot.width - room.width + 1, step):
            for y in range(0, plot.height - room.height + 1, step):
                room.x, room.y = x, y
                if not check_collision(room, placed, plot, tolerance, bounds_tolerance):
                    candidates.append((x, y, 'interior', 20))
    
    return candidates


def improved_boundary_pack(rooms, plot, corridor_width=3, corridor_prob=0.3, seed=None, 
                           max_attempts=5, allow_overlap_final=False):
    """
    Improved boundary packing that maintains corridor structure while maximizing room placement.
    
    Args:
        rooms: List of Room objects
        plot: Plot object
        corridor_width: Width of corridors between rooms
        corridor_prob: Probability of adding corridor spacing
        seed: Random seed for reproducibility
        max_attempts: Number of different placement orders to try
        allow_overlap_final: Allow small overlaps in final attempt
    """
    if seed is not None:
        random.seed(seed)
    
    best_layout = None
    best_score = -1
    best_unplaced = rooms
    
    # Try multiple strategies
    for attempt in range(max_attempts):
        rooms_copy = copy.deepcopy(rooms)
        
        # Strategy for ordering rooms
        if attempt == 0:
            # Largest first (best for maintaining corridors)
            rooms_copy.sort(key=lambda r: r.area(), reverse=True)
        elif attempt == 1:
            # Perimeter-friendly: longest dimension first
            rooms_copy.sort(key=lambda r: max(r.width, r.height), reverse=True)
        elif attempt == 2:
            # Mixed: large rooms with some randomness
            rooms_copy.sort(key=lambda r: r.area() + random.randint(-10, 30), reverse=True)
        elif attempt == 3:
            # Aspect ratio: prefer rooms that fit edges better
            rooms_copy.sort(key=lambda r: min(r.width, r.height) / max(r.width, r.height, 0.1), reverse=True)
        else:
            # Random order
            random.shuffle(rooms_copy)
        
        placed = []
        unplaced = []
        
        # Try to place each room
        for room in rooms_copy:
            placed_successfully = False
            
            # Try both orientations
            for rotation_attempt in [0, 1]:
                if rotation_attempt == 1:
                    room.rotate()
                
                # Find candidate positions with corridor awareness
                allow_overlap = allow_overlap_final and (attempt == max_attempts - 1)
                candidates = find_all_candidate_positions(room, placed, plot, 
                                                         corridor_width, corridor_prob, allow_overlap)
                
                if candidates:
                    # Sort candidates by priority and strategy
                    # Prefer: first room > adjacent > boundary > interior
                    candidates.sort(key=lambda c: (-c[3], random.random()))
                    
                    # Choose best candidate with slight randomness for variety
                    if len(candidates) > 1 and random.random() < 0.2:
                        # 20% chance to pick from top 3 candidates
                        x, y, strategy, priority = random.choice(candidates[:min(3, len(candidates))])
                    else:
                        x, y, strategy, priority = candidates[0]
                    
                    room.x, room.y = x, y
                    placed.append(room)
                    placed_successfully = True
                    break
            
            if not placed_successfully:
                room.reset_rotation()
                unplaced.append(room)
        
        # Calculate score for this layout
        score = calculate_layout_score(placed, plot, corridor_width)
        
        # Bonus for maintaining corridor structure (check spacing between adjacent rooms)
        corridor_bonus = 0
        for i, r1 in enumerate(placed):
            for r2 in placed[i+1:]:
                # Check if rooms are aligned horizontally or vertically
                if abs(r1.y - r2.y) < 1 and abs(r1.x + r1.width - r2.x) <= corridor_width + 1:
                    corridor_bonus += 50  # Horizontal alignment with proper spacing
                elif abs(r1.x - r2.x) < 1 and abs(r1.y + r1.height - r2.y) <= corridor_width + 1:
                    corridor_bonus += 50  # Vertical alignment with proper spacing
        
        score += corridor_bonus
        
        # Keep the best layout
        if score > best_score:
            best_score = score
            best_layout = placed
            best_unplaced = unplaced
    
    return best_layout, best_unplaced


# ------------------ Main function for compatibility ------------------ #

def boundary_pack_revised(rooms, plot, corridor_width=3, corridor_prob=0.3, seed=None):
    """Wrapper function for backward compatibility with UI."""
    return improved_boundary_pack(rooms, plot, corridor_width, corridor_prob, seed, 
                                 max_attempts=5, allow_overlap_final=False)
