# Enhanced Scoring Algorithm Explanation

## Problem Statement

Given:

- A list of rooms with width and height
- A rectilinear plot boundary
- Rooms total area ≤ 70% of plot area
- Remaining 30% for circulation/corridors (3 units wide)
- Room rotation (swap width/height) is allowed

Goal: Arrange rooms within plot boundary while creating proper circulation with ALL rooms connected

---

## Enhanced Scoring Algorithm (Priority Order)

### 🥇 **PRIORITY 1: Place All Rooms (10,000 pts per room)**

```python
score += len(placed) * 10,000
```

**Why it's first:**

- The primary goal is to fit all rooms
- A layout with 13/13 rooms scores 130,000 points from this alone
- A layout with 12/13 rooms scores only 120,000 points
- This 10,000 point difference ensures placing all rooms is always preferred

**Example:**

- Layout A: 13 rooms, poor corridors → Base: 130,000 pts
- Layout B: 12 rooms, perfect corridors → Base: 120,000 pts
- Layout A wins (before considering other factors)

---

### 🚨 **PRIORITY 2: ALL Rooms MUST Be Connected (-5,000 pts per disconnected room)**

**NEW CRITICAL REQUIREMENT**: Every room must be reachable from every other room via corridors.

```python
# Build corridor network graph
for each pair of adjacent rooms:
    if gap ≈ corridor_width:
        add_edge_to_graph(room1, room2)

# Check connectivity using BFS
connected_rooms = find_connected_component()
disconnected_count = total_rooms - connected_rooms

if disconnected_count > 0:
    score -= disconnected_count * 5,000  # HEAVY PENALTY
    print(f"WARNING: {disconnected_count} rooms not connected!")
else:
    score += 2,000  # Bonus for full connectivity
```

**Why this is critical:**

- **-5,000 penalty** per disconnected room
- A layout with 1 disconnected room loses 5,000 points
- This is HALF the value of placing one room
- Ensures isolated rooms are heavily penalized
- Bonus +2,000 when all rooms are properly connected

**Example:**

```
Layout A: 13 rooms, 1 disconnected
Score: 130,000 (rooms) - 5,000 (disconnected) = 125,000

Layout B: 12 rooms, all connected
Score: 120,000 (rooms) + 2,000 (bonus) = 122,000

Layout A still wins but the gap narrowed significantly
```

---

### 🥈 **PRIORITY 3: Direct Room-to-Room Connectivity (500 pts per direct connection)**

**NEW**: Treats corridors as edges in a graph. Rewards layouts where rooms connect directly (within 1 edge hop).

```python
# For each pair of rooms:
if rooms_aligned_horizontally and gap ≈ corridor_width:
    adjacency[room1].add(room2)
    adjacency[room2].add(room1)

    # Score based on corridor quality
    if gap == EXACTLY corridor_width:
        score += 500  # Perfect direct connection
    elif abs(gap - corridor_width) < 0.5:
        score += 300  # Good connection
    else:
        score += 150  # Acceptable connection

# Calculate average connectivity
avg_connections = sum(len(neighbors) for neighbors) / num_rooms

if avg_connections >= 3.5:
    score += 1,500  # Each room connects to 3-4 others (excellent!)
elif avg_connections >= 2.5:
    score += 1,000  # Each room connects to 2-3 others (good)
elif avg_connections >= 1.5:
    score += 500   # Each room connects to 1-2 others (decent)
elif avg_connections >= 1.0:
    score += 200   # Minimal connectivity
else:
    score -= 500   # Poor connectivity
```

**What this achieves:**

- Rewards layouts where rooms have multiple direct corridor connections
- Encourages "grid-like" layouts with cross-connections
- Penalizes "chain" layouts where rooms connect in a single line

**Example:**

```
Good Layout (Grid):
[Room1]--3--[Room2]--3--[Room3]
   |            |            |
   3            3            3
   |            |            |
[Room4]--3--[Room5]--3--[Room6]

Room5 connects to: Room2, Room4, Room6 (3 connections)
Average: 2.5 connections → +1,000 pts + individual corridor bonuses
```

---

### 🥉 **PRIORITY 4: Minimize Choke Points (up to 2,000 pts)**

Evaluates accessibility from each room in all 4 directions.

```python
for each room:
    accessible_directions = count_directions_with_corridor_width_clearance()

    if accessible_directions >= 3:
        score += 250  # Excellent (hub room)
    elif accessible_directions == 2:
        score += 150  # Good (corridor room)
    elif accessible_directions == 1:
        score -= 200  # Dead end (increased penalty)
    else:
        score -= 500  # Trapped room (severe penalty)
```

**Enhanced penalties:**

- Dead ends now penalized more heavily (-200 vs -100)
- Trapped rooms severely penalized (-500 vs -300)
- Better rewards for accessible rooms (+250 vs +200)

**Visual Example:**

```
Good Layout (250 pts per room):
    ↑ Clear
    |
← [Room] → Clear
    |
    ↓ Clear
3 directions accessible
```

```
Poor Layout (-100 pts):
    X Blocked
    |
← [Room] X Blocked
    |
    ↓ Clear
Only 1 direction (dead end)
```

**What counts as "clear":**

- No other room blocking within 3 units
- OR touches plot boundary (considered accessible)

---

### 🏅 **PRIORITY 4: Continuous Corridor Paths (up to 3,000 pts)**

Uses graph theory to check if all rooms are connected by proper 3-unit corridors.

#### 4a. Connectivity Check (up to 3,000 pts)

```python
# Build graph: rooms = nodes, 3-unit corridors = edges
adjacency_graph = build_corridor_network()

# Check if all rooms reachable from any starting room
connectivity_ratio = reachable_rooms / total_rooms
score += connectivity_ratio * 3,000

# Example:
# 13/13 rooms connected → +3,000 pts
# 10/13 rooms connected → +2,307 pts
```

#### 4b. Redundancy Bonus (up to 1,000 pts)

```python
avg_connections = average_corridors_per_room

if avg_connections >= 3:
    score += 1,000  # Multiple paths available
elif avg_connections >= 2:
    score += 500   # Decent alternative routes
```

**Why this matters:**

- Prevents single "bottleneck" corridors
- Ensures multiple paths between rooms
- More realistic circulation patterns

**Example Network:**

```
Excellent (avg = 3 connections):
    A --- B --- C
    |     |     |
    D --- E --- F

Each room has 2-4 connections
Score: +1,000 bonus
```

```
Poor (avg = 1.5 connections):
    A --- B --- C --- D --- E --- F

Linear chain, single path
Score: +0 bonus
```

---

### 🎯 **PRIORITY 5: Space Utilization ~70% (up to 1,000 pts)**

Targets exactly 70% room area, 30% circulation.

```python
utilization = total_room_area / plot_area
target = 0.70
diff = |utilization - target|

if diff < 0.05:    # 65%-75%
    score += 1,000  # Perfect
elif diff < 0.10:  # 60%-80%
    score += 500    # Good
else:
    score -= diff * 500  # Penalty increases with distance
```

**Examples:**

- 68% utilization → diff = 0.02 → +1,000 pts ✓
- 55% utilization → diff = 0.15 → -75 pts (wasted space)
- 85% utilization → diff = 0.15 → -75 pts (not enough circulation)

---

## Additional Quality Metrics

### Grid Regularity (up to 300 pts)

```python
# Count unique X and Y coordinates
unique_coords = len(x_coords) + len(y_coords)
regularity = 1000 / unique_coords
score += regularity * 300
```

**Prefers aligned layouts:**

```
Regular (12 unique coords):          Irregular (30 unique coords):
+---+---+---+                        +--+----+--+
| A | B | C |                        |A |  B   |C|
+---+---+---+                        +--+--+---+-+
| D | E | F |                        | D|E |F| G |
+---+---+---+                        +--+--+-+---+
Score: +300/12 * 300 = +25          Score: +1000/30 * 300 = +10
```

### Edge Alignment (20 pts per edge)

```python
for room in placed:
    if room touches left/right edge:
        score += 20
    if room touches top/bottom edge:
        score += 20
```

Rewards boundary utilization (up to 40 pts per room).

---

## Total Score Breakdown

For a **perfect 13/13 layout** with excellent corridors:

| Component            | Points       | Explanation          |
| -------------------- | ------------ | -------------------- |
| 13 rooms placed      | 130,000      | 10,000 × 13          |
| 20 proper corridors  | 10,000       | 500 × 20             |
| All rooms accessible | 2,600        | 200 × 13             |
| Full connectivity    | 3,000        | 100% connected       |
| Multiple paths bonus | 1,000        | avg ≥ 3 connections  |
| 70% utilization      | 1,000        | Within 5% of target  |
| Grid regularity      | 300          | Aligned layout       |
| Edge alignment       | 520          | 13 rooms × 40 avg    |
| **TOTAL**            | **~148,420** | **Excellent layout** |

For a **13/13 layout** with poor corridors:

| Component            | Points       | Explanation               |
| -------------------- | ------------ | ------------------------- |
| 13 rooms placed      | 130,000      | 10,000 × 13               |
| 10 narrow corridors  | 1,000        | 100 × 10 (with penalties) |
| Some dead ends       | -500         | 5 rooms with 1 exit       |
| Partial connectivity | 1,500        | 50% connected             |
| No path redundancy   | 0            | Linear layout             |
| 60% utilization      | -500         | Too much wasted space     |
| Poor regularity      | 50           | Random placement          |
| Edge alignment       | 260          | Some boundary use         |
| **TOTAL**            | **~131,810** | **Poor quality**          |

**Difference: 16,610 points** - This ensures quality matters after all rooms are placed!

---

## Summary

1. **First**: Place all rooms (dominates with 10,000 pts each)
2. **Then**: Optimize corridor quality
   - Prefer 3-unit wide corridors
   - Minimize choke points (narrow passages)
   - Ensure continuous connectivity (all rooms reachable)
   - Create multiple paths (avoid bottlenecks)
3. **Finally**: Fine-tune utilization, regularity, and edge alignment

This ensures the algorithm:
✓ Places all rooms first
✓ Creates proper 3-unit circulation
✓ Avoids dead ends and bottlenecks
✓ Ensures continuous connectivity
✓ Targets ~70% utilization
