# Corridor Width Detection - Detailed Explanation

## How Corridors Are Measured

The algorithm detects corridors by measuring the **gap between adjacent rooms**. There are two types:

---

## 1. Horizontal Corridors (Side-by-Side Rooms)

### Visual Example:

```
     Y
     ↑
     |
  5  |  ┌─────────┐              ┌─────────┐
     |  │  Room1  │    GAP=3     │  Room2  │
  0  |  └─────────┘ ←──────────→ └─────────┘
     |
     └──────────────────────────────────────→ X
        0         10            13          21
```

### Detection Logic:

```python
# Step 1: Check if rooms are aligned vertically (similar Y coordinates)
if abs(r1.y - r2.y) < 0.5:  # Both rooms have Y ≈ 0

    # Step 2: Calculate horizontal gap
    # Gap = distance between right edge of left room and left edge of right room
    gap = r2.x - (r1.x + r1.width)
    # gap = 13 - (0 + 10) = 3 units ✓

    # Step 3: Check if gap is reasonable (within corridor_width tolerance)
    if 0 < gap <= corridor_width + 1:  # 0 < 3 <= 4
        # This is a corridor!
        if abs(gap - corridor_width) < 0.1:  # |3 - 3| < 0.1
            score += 500  # Perfect corridor (exact width)
```

### What Counts as "Aligned"?

Rooms are considered aligned if:

- Their bottom edges match: `abs(r1.y - r2.y) < 0.5`
- OR their top edges match: `abs((r1.y + r1.height) - (r2.y + r2.height)) < 0.5`

Example:

```
Aligned (bottom edges):
┌─────────┐     ┌─────────┐
│  Room1  │  3  │  Room2  │
│         │     │         │
└─────────┘     └─────────┘  ← Both at Y=0
   ✓ Horizontal corridor detected

Not aligned (offset):
┌─────────┐
│  Room1  │  3  ┌─────────┐
│         │     │  Room2  │
└─────────┘     └─────────┘
   ✗ No corridor (Y coordinates differ)
```

---

## 2. Vertical Corridors (Stacked Rooms)

### Visual Example:

```
     Y
     ↑
     |
 20  |  ┌─────────┐
     |  │  Room2  │
 15  |  └─────────┘
     |      ↕ GAP=3
 12  |  ┌─────────┐
     |  │  Room1  │
  5  |  │         │
     |  └─────────┘
  0  |
     └──────────────────────→ X
        0         10
```

### Detection Logic:

```python
# Step 1: Check if rooms are aligned horizontally (similar X coordinates)
if abs(r1.x - r2.x) < 0.5:  # Both rooms have X ≈ 0

    # Step 2: Calculate vertical gap
    # Gap = distance between top edge of bottom room and bottom edge of top room
    gap = r2.y - (r1.y + r1.height)
    # gap = 15 - (5 + 7) = 3 units ✓

    # Step 3: Check if gap is reasonable
    if 0 < gap <= corridor_width + 1:  # 0 < 3 <= 4
        # This is a corridor!
        if abs(gap - corridor_width) < 0.1:  # |3 - 3| < 0.1
            score += 500  # Perfect corridor
```

### What Counts as "Aligned"?

Rooms are considered aligned if:

- Their left edges match: `abs(r1.x - r2.x) < 0.5`
- OR their right edges match: `abs((r1.x + r1.width) - (r2.x + r2.width)) < 0.5`

---

## Scoring Based on Gap Width

The algorithm scores corridors based on how close they are to the **target corridor width** (set in UI):

### Scenario 1: Perfect Width (Score: +500)

```
Gap = exactly corridor_width (e.g., 3 units)

Room1 [10x5]  ← 3 units →  Room2 [8x5]

Score: +200 (base) + +300 (perfect width) = +500 points
```

### Scenario 2: Acceptable Width (Score: +200)

```
Gap = 2.6 to 4 units (close to target)

Room1 [10x5]  ← 3.5 units →  Room2 [8x5]

Score: +200 (base) = +200 points
```

### Scenario 3: Choke Point (Score: +100)

```
Gap = less than corridor_width - 0.5 (too narrow!)

Room1 [10x5]  ← 2 units →  Room2 [8x5]
               (NARROW!)

Score: +200 (base) - 100 (choke penalty) = +100 points
```

### Scenario 4: Too Wide (Score: 0)

```
Gap > corridor_width + 1 (not considered a corridor)

Room1 [10x5]  ← 5 units →  Room2 [8x5]
               (TOO WIDE)

Score: 0 points (not a corridor)
```

---

## Complete Example: L-Shaped Layout

```
     Y
     ↑
     |
 30  |  ┌─────────┐
     |  │ Room3   │
 24  |  └─────────┘
     |      ↕ 3    (Vertical corridor)
 21  |  ┌─────────┐              ┌─────────┐
     |  │ Room2   │      3       │ Room4   │
 15  |  └─────────┘ ←──────────→ └─────────┘
     |      ↕ 3    (Horz corridor)
 12  |  ┌─────────┐
     |  │ Room1   │
  5  |  │         │
     |  └─────────┘
  0  |
     └──────────────────────────────────────→ X
        0         10            13          21
```

### Detected Corridors:

1. **Vertical: Room1 ↔ Room2**

   - Room1 top: Y = 12
   - Room2 bottom: Y = 15
   - Gap: 15 - 12 = 3 ✓
   - X alignment: Both at X=0 ✓
   - Score: +500 (perfect width)

2. **Vertical: Room2 ↔ Room3**

   - Room2 top: Y = 21
   - Room3 bottom: Y = 24
   - Gap: 24 - 21 = 3 ✓
   - X alignment: Both at X=0 ✓
   - Score: +500 (perfect width)

3. **Horizontal: Room2 ↔ Room4**
   - Room2 right: X = 10
   - Room4 left: X = 13
   - Gap: 13 - 10 = 3 ✓
   - Y alignment: Both at Y=15 ✓
   - Score: +500 (perfect width)

**Total corridor score: +1,500 points**

---

## Why Use corridor_width + 1 as Maximum?

```python
if 0 < gap <= corridor_width + 1:
```

This allows a **1-unit tolerance** because:

1. Rooms may be slightly offset due to rounding
2. Allows corridors of width 3-4 units (both acceptable)
3. Prevents counting very wide gaps (>4 units) as corridors

---

## Common Issues and Detection

### Issue 1: Offset Rooms (No Corridor Detected)

```
┌─────────┐
│  Room1  │     ┌─────────┐
│         │  3  │  Room2  │  ← Offset by 2 units
└─────────┘     └─────────┘

Y coordinates differ by 2 units
abs(r1.y - r2.y) = 2 (not < 0.5)
✗ Not detected as corridor
```

### Issue 2: Diagonal Arrangement (No Corridor)

```
┌─────────┐
│  Room1  │
└─────────┘
            ┌─────────┐
            │  Room2  │
            └─────────┘

Neither X nor Y coordinates align
✗ No corridor (diagonal placement)
```

### Issue 3: Rooms Too Far Apart

```
┌─────────┐           ┌─────────┐
│  Room1  │  ← 8 →    │  Room2  │
└─────────┘           └─────────┘

Gap = 8 units (> corridor_width + 1 = 4)
✗ Not considered a corridor (too wide)
```

---

## Summary

### Corridor Detection Requirements:

1. ✓ Rooms must be **aligned** (horizontal OR vertical)
2. ✓ Gap must be **> 0** (not touching)
3. ✓ Gap must be **≤ corridor_width + 1** (not too wide)

### Scoring:

- **+500 pts**: Gap = exactly corridor_width (perfect)
- **+200 pts**: Gap ≈ corridor_width (acceptable)
- **+100 pts**: Gap < corridor_width - 0.5 (choke point)
- **0 pts**: Gap > corridor_width + 1 (too wide)

### The UI Variable:

The `corridor_width` value from the UI (default: 3) is used throughout:

- In `improved_boundary_pack()` for placement spacing
- In `calculate_layout_score()` for scoring corridors
- In `find_all_candidate_positions()` for position calculation

**No hardcoded values!** Everything uses the UI input. ✓
