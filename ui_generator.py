import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import matplotlib
matplotlib.use('TkAgg')  # Set backend before importing pyplot
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.patches as patches
from generator_improved import Room, Plot, improved_boundary_pack, calculate_layout_score
import random
import copy
import json
from datetime import datetime
import time
import threading
import sys
import ctypes

# Enable DPI awareness for Windows text scaling
if sys.platform == 'win32':
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)  # Windows 8.1+
    except:
        try:
            ctypes.windll.user32.SetProcessDPIAware()  # Windows Vista+
        except:
            pass


class GeneratorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Boundary Packing Floor Plan Generator")
        
        # Enable scaling for high DPI displays
        self.root.tk.call('tk', 'scaling', self.root.winfo_fpixels('1i') / 72.0)
        
        self.root.state('zoomed')
        
        # Data storage
        self.rooms = []
        self.plot = None
        self.current_layout = None
        self.placed_rooms = []
        self.unplaced_rooms = []
        
        # Configuration variables
        self.corridor_width = tk.IntVar(value=3)
        self.corridor_prob = tk.DoubleVar(value=0.3)
        self.seed_value = tk.IntVar(value=0)
        self.use_seed = tk.BooleanVar(value=True)
        
        # Continuous generation variables
        self.is_generating = False
        self.generation_thread = None
        self.best_layout_ever = None
        self.best_score_ever = -1
        self.attempts_count = 0
        self.all_layouts = []  # Store all generated layouts with scores
        self.top_layouts = []  # Top 100 layouts
        self.used_seeds = set()  # Track used seeds to avoid duplicates
        
        # Initialize UI
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the main UI layout"""
        # Main container with left panel and right canvas
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left panel for controls
        left_panel = ttk.Frame(main_container, width=400)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 10))
        left_panel.pack_propagate(False)
        
        # Right panel for visualization
        right_panel = ttk.Frame(main_container)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Setup sections
        self.setup_file_operations(left_panel)
        self.setup_plot_section(left_panel)
        self.setup_rooms_section(left_panel)
        self.setup_config_section(left_panel)
        self.setup_generation_section(left_panel)
        self.setup_stats_section(left_panel)
        self.setup_canvas(right_panel)
        
    def setup_file_operations(self, parent):
        """Setup file save/load operations section"""
        frame = ttk.LabelFrame(parent, text="File Operations", padding=10)
        frame.pack(fill=tk.X, pady=(0, 10))
        
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X)
        
        ttk.Button(btn_frame, text="💾 Save Input", command=self.save_input_file).pack(
            side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        ttk.Button(btn_frame, text="📂 Load Input", command=self.load_input_file).pack(
            side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        
    def setup_plot_section(self, parent):
        """Setup plot configuration section"""
        frame = ttk.LabelFrame(parent, text="Plot Configuration", padding=10)
        frame.pack(fill=tk.X, pady=(0, 10))
        
        # Width
        ttk.Label(frame, text="Plot Width:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.plot_width_entry = ttk.Entry(frame, width=15)
        self.plot_width_entry.insert(0, "25")
        self.plot_width_entry.grid(row=0, column=1, pady=5, padx=5)
        
        # Height
        ttk.Label(frame, text="Plot Height:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.plot_height_entry = ttk.Entry(frame, width=15)
        self.plot_height_entry.insert(0, "11")
        self.plot_height_entry.grid(row=1, column=1, pady=5, padx=5)
        
        # Set Plot button
        ttk.Button(frame, text="Set Plot", command=self.set_plot).grid(
            row=2, column=0, columnspan=2, pady=10)
            
    def setup_rooms_section(self, parent):
        """Setup rooms management section"""
        frame = ttk.LabelFrame(parent, text="Rooms Management", padding=10)
        frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Input frame
        input_frame = ttk.Frame(frame)
        input_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(input_frame, text="Name:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.room_name_entry = ttk.Entry(input_frame, width=12)
        self.room_name_entry.grid(row=0, column=1, pady=5, padx=5)
        
        ttk.Label(input_frame, text="Width:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.room_width_entry = ttk.Entry(input_frame, width=12)
        self.room_width_entry.grid(row=1, column=1, pady=5, padx=5)
        
        ttk.Label(input_frame, text="Height:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.room_height_entry = ttk.Entry(input_frame, width=12)
        self.room_height_entry.grid(row=2, column=1, pady=5, padx=5)
        
        # Buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(btn_frame, text="Add Room", command=self.add_room).pack(
            side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Remove Selected", command=self.remove_room).pack(
            side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Clear All", command=self.clear_rooms).pack(
            side=tk.LEFT, padx=2)
        
        # Load example button
        ttk.Button(frame, text="Load Example Rooms", command=self.load_example).pack(
            fill=tk.X, pady=(0, 10))
        
        # Rooms list
        ttk.Label(frame, text="Rooms List:").pack(anchor=tk.W)
        
        list_frame = ttk.Frame(frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.rooms_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, height=8)
        self.rooms_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.rooms_listbox.yview)
        
    def setup_config_section(self, parent):
        """Setup generation configuration section"""
        frame = ttk.LabelFrame(parent, text="Generation Settings", padding=10)
        frame.pack(fill=tk.X, pady=(0, 10))
        
        # Corridor Width
        ttk.Label(frame, text="Corridor Width:").grid(row=0, column=0, sticky=tk.W, pady=5)
        corridor_spin = ttk.Spinbox(frame, from_=0, to=10, textvariable=self.corridor_width, 
                                     width=13)
        corridor_spin.grid(row=0, column=1, pady=5, padx=5)
        
        # Corridor Probability
        ttk.Label(frame, text="Corridor Probability:").grid(row=1, column=0, sticky=tk.W, pady=5)
        prob_spin = ttk.Spinbox(frame, from_=0.0, to=1.0, increment=0.1, 
                                textvariable=self.corridor_prob, width=13)
        prob_spin.grid(row=1, column=1, pady=5, padx=5)
        
        # Seed settings
        seed_check = ttk.Checkbutton(frame, text="Use Seed", variable=self.use_seed,
                                     command=self.toggle_seed)
        seed_check.grid(row=2, column=0, sticky=tk.W, pady=5)
        
        self.seed_entry = ttk.Spinbox(frame, from_=0, to=9999, textvariable=self.seed_value, 
                                      width=13)
        self.seed_entry.grid(row=2, column=1, pady=5, padx=5)
        
    def setup_generation_section(self, parent):
        """Setup generation controls"""
        frame = ttk.LabelFrame(parent, text="Generation Controls", padding=10)
        frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(frame, text="Generate Layout", command=self.generate_layout,
                  style='Accent.TButton').pack(fill=tk.X, pady=5)
        
        # Continuous generation button with indicator
        continuous_frame = ttk.Frame(frame)
        continuous_frame.pack(fill=tk.X, pady=5)
        
        self.continuous_btn = ttk.Button(continuous_frame, 
                                         text="🔄 Generate Continuous (1 min)",
                                         command=self.toggle_continuous_generation)
        self.continuous_btn.pack(fill=tk.X)
        
        # Status label for continuous generation
        self.generation_status = ttk.Label(frame, text="", foreground="blue")
        self.generation_status.pack(fill=tk.X, pady=2)
        
        # View top layouts button
        self.view_top_btn = ttk.Button(frame, text="📊 View Top 100 Layouts",
                                       command=self.show_top_layouts_window,
                                       state='disabled')
        self.view_top_btn.pack(fill=tk.X, pady=5)
        
        ttk.Button(frame, text="Clear Visualization", command=self.clear_canvas).pack(
            fill=tk.X, pady=5)
            
    def setup_stats_section(self, parent):
        """Setup statistics display section"""
        frame = ttk.LabelFrame(parent, text="Statistics", padding=10)
        frame.pack(fill=tk.X, pady=(0, 10))
        
        self.stats_text = scrolledtext.ScrolledText(frame, height=8, width=40, 
                                                     state='disabled', wrap=tk.WORD)
        self.stats_text.pack(fill=tk.BOTH, expand=True)
        
    def setup_canvas(self, parent):
        """Setup matplotlib canvas for visualization"""
        canvas_frame = ttk.LabelFrame(parent, text="Floor Plan Visualization", padding=10)
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create matplotlib figure
        self.fig, self.ax = plt.subplots(figsize=(10, 8))
        self.canvas = FigureCanvasTkAgg(self.fig, master=canvas_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Initial empty plot
        self.clear_canvas()
        
    def toggle_seed(self):
        """Toggle seed entry state"""
        state = 'normal' if self.use_seed.get() else 'disabled'
        self.seed_entry.config(state=state)
        
    def set_plot(self):
        """Set plot dimensions"""
        try:
            width = int(self.plot_width_entry.get())
            height = int(self.plot_height_entry.get())
            
            if width <= 0 or height <= 0:
                messagebox.showerror("Error", "Plot dimensions must be positive!")
                return
                
            self.plot = Plot(width, height)
            messagebox.showinfo("Success", f"Plot set to {width}x{height}")
            self.update_stats()
            
        except ValueError:
            messagebox.showerror("Error", "Invalid plot dimensions!")
            
    def add_room(self):
        """Add a room to the list"""
        try:
            name = self.room_name_entry.get().strip()
            width = int(self.room_width_entry.get())
            height = int(self.room_height_entry.get())
            
            if not name:
                messagebox.showerror("Error", "Room name cannot be empty!")
                return
                
            if width <= 0 or height <= 0:
                messagebox.showerror("Error", "Room dimensions must be positive!")
                return
                
            # Check for duplicate names
            if any(r.name == name for r in self.rooms):
                messagebox.showerror("Error", f"Room '{name}' already exists!")
                return
                
            room = Room(width, height, name)
            self.rooms.append(room)
            self.rooms_listbox.insert(tk.END, f"{name} ({width}x{height})")
            
            # Clear entries
            self.room_name_entry.delete(0, tk.END)
            self.room_width_entry.delete(0, tk.END)
            self.room_height_entry.delete(0, tk.END)
            
            self.update_stats()
            
        except ValueError:
            messagebox.showerror("Error", "Invalid room dimensions!")
            
    def remove_room(self):
        """Remove selected room"""
        selection = self.rooms_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a room to remove!")
            return
            
        idx = selection[0]
        self.rooms.pop(idx)
        self.rooms_listbox.delete(idx)
        self.update_stats()
        
    def clear_rooms(self):
        """Clear all rooms"""
        if self.rooms and not messagebox.askyesno("Confirm", "Clear all rooms?"):
            return
            
        self.rooms.clear()
        self.rooms_listbox.delete(0, tk.END)
        self.update_stats()
        
    def load_example(self):
        """Load example rooms"""
        self.rooms.clear()
        self.rooms_listbox.delete(0, tk.END)
        
        example_rooms = [
            (6, 4, "Living Room"),
            (5, 5, "Kitchen"),
            (3, 6, "Bedroom 1"),
            (4, 4, "Bedroom 2"),
            (8, 4, "Master Bedroom"),
            (3, 5, "Bathroom"),
            (7, 3, "Dining"),
            (5, 5, "Office"),
        ]
        
        for width, height, name in example_rooms:
            room = Room(width, height, name)
            self.rooms.append(room)
            self.rooms_listbox.insert(tk.END, f"{name} ({width}x{height})")
            
        messagebox.showinfo("Success", "Example rooms loaded!")
        self.update_stats()
        
    def generate_layout(self):
        """Generate a single layout"""
        if not self.validate_generation():
            return
            
        # Get seed if enabled
        seed = self.seed_value.get() if self.use_seed.get() else None
        
        # Generate layout using improved algorithm
        placed, unplaced = improved_boundary_pack(
            self.rooms, 
            self.plot,
            corridor_width=self.corridor_width.get(),
            corridor_prob=self.corridor_prob.get(),
            seed=seed,
            max_attempts=5,
            allow_overlap_final=False
        )
        
        self.placed_rooms = placed
        self.unplaced_rooms = unplaced
        
        # Visualize
        self.visualize_layout(placed, unplaced, "Current Layout")
        self.update_stats_after_generation(placed, unplaced)
        
    def toggle_continuous_generation(self):
        """Toggle continuous generation on/off"""
        if self.is_generating:
            # Stop generation
            self.is_generating = False
            self.continuous_btn.config(text="🔄 Generate Continuous (1 min)")
            self.generation_status.config(text="Stopped", foreground="red")
        else:
            # Start generation
            if not self.validate_generation():
                return
            self.start_continuous_generation()
            
    def start_continuous_generation(self):
        """Start continuous generation in a separate thread"""
        self.is_generating = True
        self.best_layout_ever = None
        self.best_score_ever = -1
        self.attempts_count = 0
        self.all_layouts = []  # Reset layouts list
        self.top_layouts = []
        self.used_seeds = set()  # Reset used seeds tracker
        
        self.continuous_btn.config(text="⏹ Stop Generation")
        self.generation_status.config(text="Initializing...", foreground="blue")
        self.view_top_btn.config(state='disabled')
        
        # Start generation thread
        self.generation_thread = threading.Thread(target=self.continuous_generation_worker, daemon=True)
        self.generation_thread.start()
        
    def continuous_generation_worker(self):
        """Worker function for continuous generation"""
        from generator_improved import calculate_layout_score
        
        start_time = time.time()
        max_duration = 60  # 1 minute total
        update_interval = 2  # Update display every 2 seconds
        last_update = start_time
        
        try:
            while self.is_generating and (time.time() - start_time) < max_duration:
                # Generate a unique seed (avoid duplicates)
                max_attempts_for_seed = 10
                seed = None
                for _ in range(max_attempts_for_seed):
                    candidate_seed = random.randint(0, 999999999)  # Much larger range (1 billion)
                    if candidate_seed not in self.used_seeds:
                        seed = candidate_seed
                        self.used_seeds.add(seed)
                        break
                
                # If we couldn't find a unique seed (unlikely), skip this iteration
                if seed is None:
                    continue
                
                # Generate layout with improved algorithm
                placed, unplaced = improved_boundary_pack(
                    self.rooms,
                    self.plot,
                    corridor_width=self.corridor_width.get(),
                    corridor_prob=self.corridor_prob.get(),
                    seed=seed,
                    max_attempts=5,
                    allow_overlap_final=False
                )
                
                self.attempts_count += 1
                
                # Calculate detailed score (uses corridor_width from UI)
                score = calculate_layout_score(placed, self.plot, self.corridor_width.get())
                
                # Store this layout
                self.all_layouts.append({
                    'placed': copy.deepcopy(placed),
                    'unplaced': copy.deepcopy(unplaced),
                    'seed': seed,
                    'score': score,
                    'num_placed': len(placed)
                })
                
                # Update best layout if this one is better (by score, not just count)
                if score > self.best_score_ever:
                    self.best_score_ever = score
                    self.best_layout_ever = (placed, unplaced, seed)
                    
                    # Update UI immediately when we find a better layout
                    self.root.after(0, self.update_best_layout_ui)
                
                # Update status every 2 seconds
                current_time = time.time()
                if current_time - last_update >= update_interval:
                    elapsed = int(current_time - start_time)
                    remaining = max_duration - elapsed
                    self.root.after(0, self.update_generation_status, 
                                  elapsed, remaining, self.attempts_count, self.best_score_ever, len(placed))
                    last_update = current_time
            
            # Finished - process top 100 layouts
            self.root.after(0, self.process_top_layouts)
            
            # Update final status
            total_time = time.time() - start_time
            self.root.after(0, self.finish_continuous_generation, total_time)
            
        except Exception as e:
            
            print(f"Generation complete: {self.attempts_count} total attempts")
            
            # Finished - process top 100 layouts
            self.root.after(0, self.process_top_layouts)
            
            # Update final status
            total_time = time.time() - start_time
            self.root.after(0, self.finish_continuous_generation, total_time)
            
        except Exception as e:
            self.root.after(0, self.generation_error, str(e))
            
    def update_generation_status(self, elapsed, remaining, attempts, best_score, num_placed):
        """Update the generation status label"""
        if self.is_generating:
            status = f"⏱ {remaining}s left | Attempts: {attempts} | Best: {num_placed}/{len(self.rooms)} rooms (Score: {best_score:.0f})"
            self.generation_status.config(text=status, foreground="blue")
            
    def update_best_layout_ui(self):
        """Update UI with the current best layout"""
        if self.best_layout_ever:
            placed, unplaced, seed = self.best_layout_ever
            self.placed_rooms = placed
            self.unplaced_rooms = unplaced
            self.visualize_layout(placed, unplaced, f"Best Layout (Seed: {seed})")
            
    def process_top_layouts(self):
        """Process and store top 100 layouts by score"""
        # Sort all layouts by score (descending)
        sorted_layouts = sorted(self.all_layouts, key=lambda x: x['score'], reverse=True)
        
        # Keep top 100
        self.top_layouts = sorted_layouts[:100]
        
        # Enable the view button
        self.view_top_btn.config(state='normal')
        
    def finish_continuous_generation(self, total_time):
        """Finish continuous generation and show results"""
        self.is_generating = False
        self.continuous_btn.config(text="🔄 Generate Continuous (1 min)")
        
        if self.best_layout_ever:
            placed, unplaced, seed = self.best_layout_ever
            self.placed_rooms = placed
            self.unplaced_rooms = unplaced
            
            status = f"✅ Complete! {self.attempts_count} attempts in {total_time:.1f}s"
            self.generation_status.config(text=status, foreground="green")
            
            self.visualize_layout(placed, unplaced, f"Best Layout (Seed: {seed})")
            self.update_stats_after_continuous(placed, unplaced, seed, self.attempts_count, total_time)
        else:
            self.generation_status.config(text="No valid layouts found", foreground="red")
            
    def generation_error(self, error_msg):
        """Handle generation error"""
        self.is_generating = False
        self.continuous_btn.config(text="🔄 Generate Continuous (1 min)")
        self.generation_status.config(text=f"Error: {error_msg}", foreground="red")
        messagebox.showerror("Generation Error", f"An error occurred:\n{error_msg}")
        
    def update_stats_after_continuous(self, placed, unplaced, seed, attempts, duration):
        """Update statistics after continuous generation"""
        total_room_area = sum(r.area() for r in self.rooms)
        placed_area = sum(r.width * r.height for r in placed)
        plot_area = self.plot.area()
        
        stats = f"Continuous Generation Results:\n\n"
        stats += f"Duration: {duration:.1f} seconds\n"
        stats += f"Attempts: {attempts}\n"
        stats += f"Best Seed: {seed}\n\n"
        stats += f"Rooms Placed: {len(placed)}/{len(self.rooms)}\n"
        stats += f"Rooms Unplaced: {len(unplaced)}\n\n"
        stats += f"Areas:\n"
        stats += f"  Plot: {plot_area} sq units\n"
        stats += f"  Placed Rooms: {placed_area} sq units\n"
        stats += f"  Circulation: {plot_area - placed_area} sq units\n"
        stats += f"  Utilization: {placed_area/plot_area*100:.1f}%\n\n"
        
        if unplaced:
            stats += f"Unplaced Rooms:\n"
            for room in unplaced:
                stats += f"  • {room.name} ({room.width}×{room.height})\n"
        else:
            stats += "✓ All rooms placed successfully!\n"
            
        self.update_stats_text(stats)
        
    def show_top_layouts_window(self):
        """Show a window with top 100 layouts"""
        if not self.top_layouts:
            messagebox.showinfo("No Data", "No layouts available. Run continuous generation first.")
            return
            
        # Create new window
        top_window = tk.Toplevel(self.root)
        top_window.title("Top 100 Layouts")
        top_window.geometry("900x700")
        
        # Header
        header_frame = ttk.Frame(top_window, padding=10)
        header_frame.pack(fill=tk.X)
        
        ttk.Label(header_frame, text=f"Top 100 Layouts from {len(self.all_layouts)} Generated", 
                 font=('Arial', 12, 'bold')).pack()
        ttk.Label(header_frame, text=f"Total Rooms: {len(self.rooms)} | Plot: {self.plot.width}×{self.plot.height}",
                 font=('Arial', 9)).pack()
        
        # Main container with list and preview
        main_container = ttk.Frame(top_window, padding=10)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Left: List of layouts
        left_frame = ttk.LabelFrame(main_container, text="Layout Rankings", padding=10)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Create treeview for layouts
        columns = ('Rank', 'Rooms', 'Score', 'Seed')
        tree = ttk.Treeview(left_frame, columns=columns, show='headings', height=25)
        
        tree.heading('Rank', text='Rank')
        tree.heading('Rooms', text='Rooms Placed')
        tree.heading('Score', text='Quality Score')
        tree.heading('Seed', text='Seed')
        
        tree.column('Rank', width=60, anchor='center')
        tree.column('Rooms', width=100, anchor='center')
        tree.column('Score', width=120, anchor='center')
        tree.column('Seed', width=100, anchor='center')
        
        # Scrollbar for treeview
        scrollbar = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Populate treeview
        for rank, layout in enumerate(self.top_layouts, 1):
            tree.insert('', tk.END, values=(
                f"#{rank}",
                f"{layout['num_placed']}/{len(self.rooms)}",
                f"{layout['score']:.0f}",
                layout['seed']
            ))
        
        # Right: Preview area
        right_frame = ttk.LabelFrame(main_container, text="Layout Preview", padding=10)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # Preview canvas
        preview_fig, preview_ax = plt.subplots(figsize=(6, 6))
        preview_canvas = FigureCanvasTkAgg(preview_fig, master=right_frame)
        preview_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Info label
        info_label = ttk.Label(right_frame, text="Click on a layout to preview", 
                              font=('Arial', 9, 'italic'))
        info_label.pack(pady=5)
        
        # Load layout button
        load_btn = ttk.Button(right_frame, text="Load Selected Layout", 
                             state='disabled')
        load_btn.pack(pady=5)
        
        selected_layout = [None]  # Use list to allow modification in nested function
        
        def on_layout_select(event):
            """Handle layout selection"""
            selection = tree.selection()
            if not selection:
                return
                
            item = tree.item(selection[0])
            rank = int(item['values'][0].replace('#', ''))
            layout = self.top_layouts[rank - 1]
            selected_layout[0] = layout
            
            # Update preview
            preview_ax.clear()
            self.draw_layout_on_axis(preview_ax, layout['placed'], layout['unplaced'], 
                                     f"Rank #{rank} | Seed: {layout['seed']}")
            preview_canvas.draw()
            
            # Update info
            info_label.config(text=f"Rank #{rank} | {layout['num_placed']}/{len(self.rooms)} rooms | Score: {layout['score']:.0f}")
            load_btn.config(state='normal')
        
        def load_selected():
            """Load the selected layout into main view"""
            if selected_layout[0]:
                layout = selected_layout[0]
                self.placed_rooms = layout['placed']
                self.unplaced_rooms = layout['unplaced']
                self.visualize_layout(layout['placed'], layout['unplaced'], 
                                     f"Loaded: Rank #{self.top_layouts.index(layout) + 1}")
                messagebox.showinfo("Success", f"Layout loaded!\nSeed: {layout['seed']}")
                top_window.destroy()
        
        tree.bind('<<TreeviewSelect>>', on_layout_select)
        load_btn.config(command=load_selected)
        
        # Export button
        export_frame = ttk.Frame(top_window, padding=10)
        export_frame.pack(fill=tk.X)
        
        ttk.Button(export_frame, text="Export Top 100 to JSON", 
                  command=lambda: self.export_top_layouts()).pack(side=tk.LEFT, padx=5)
        ttk.Button(export_frame, text="Close", 
                  command=top_window.destroy).pack(side=tk.RIGHT, padx=5)
    
    def draw_layout_on_axis(self, ax, placed, unplaced, title):
        """Draw a layout on a given matplotlib axis"""
        ax.clear()
        
        # Set limits
        ax.set_xlim(0, self.plot.width)
        ax.set_ylim(0, self.plot.height)
        ax.set_aspect('equal')
        ax.set_title(title, fontsize=9, fontweight='bold')
        
        # Draw plot boundary
        boundary = patches.Rectangle((0, 0), self.plot.width, self.plot.height,
                                     fill=False, edgecolor='black', linewidth=2)
        ax.add_patch(boundary)
        
        # Draw circulation space
        circulation = patches.Rectangle((0, 0), self.plot.width, self.plot.height,
                                       facecolor='lightgray', alpha=0.2)
        ax.add_patch(circulation)
        
        # Color palette
        colors = ['#a8e6cf', '#dcedc1', '#ffd3b6', '#ffaaa5', '#ff8b94', 
                 '#c7ceea', '#ffc8dd', '#bde0fe', '#a2d2ff', '#cdb4db']
        
        # Draw placed rooms
        for i, room in enumerate(placed):
            color = colors[i % len(colors)]
            rect = patches.Rectangle((room.x, room.y), room.width, room.height,
                                     facecolor=color, edgecolor='black', 
                                     linewidth=1, alpha=0.8)
            ax.add_patch(rect)
            
            # Room label (smaller for preview)
            ax.text(room.x + room.width/2, room.y + room.height/2,
                   f"{room.name}\n{room.width}×{room.height}",
                   ha='center', va='center', fontsize=6, fontweight='bold')
        
        # Grid
        ax.set_xticks(range(0, int(self.plot.width) + 1, max(1, int(self.plot.width//10))))
        ax.set_yticks(range(0, int(self.plot.height) + 1, max(1, int(self.plot.height//10))))
        ax.grid(True, alpha=0.2, linestyle='--')
        ax.tick_params(labelsize=7)
        
    def export_top_layouts(self):
        """Export top 100 layouts to JSON"""
        if not self.top_layouts:
            messagebox.showwarning("No Data", "No layouts to export.")
            return
            
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")],
            title="Export Top 100 Layouts",
            initialfile=f"top_100_layouts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        
        if not file_path:
            return
            
        try:
            export_data = {
                "metadata": {
                    "generated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "total_attempts": len(self.all_layouts),
                    "total_rooms": len(self.rooms),
                    "plot_size": f"{self.plot.width}×{self.plot.height}"
                },
                "layouts": []
            }
            
            for rank, layout in enumerate(self.top_layouts, 1):
                export_data["layouts"].append({
                    "rank": rank,
                    "seed": layout['seed'],
                    "score": layout['score'],
                    "rooms_placed": layout['num_placed'],
                    "rooms_unplaced": len(layout['unplaced']),
                    "placed_rooms": [
                        {
                            "name": r.name,
                            "x": r.x,
                            "y": r.y,
                            "width": r.width,
                            "height": r.height
                        }
                        for r in layout['placed']
                    ]
                })
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2)
                
            messagebox.showinfo("Success", f"Top 100 layouts exported to:\n{file_path}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export:\n{str(e)}")
    
    def generate_multiple(self):
        """Generate 3 random layouts"""
        if not self.validate_generation():
            return
            
        layouts = []
        for i in range(3):
            placed, unplaced = improved_boundary_pack(
                self.rooms,
                self.plot,
                corridor_width=self.corridor_width.get(),
                corridor_prob=self.corridor_prob.get(),
                seed=i,
                max_attempts=5,
                allow_overlap_final=False
            )
            layouts.append((placed, unplaced, i))
            
        # Show the best layout (most placed rooms)
        best_layout = max(layouts, key=lambda x: len(x[0]))
        placed, unplaced, seed = best_layout
        
        self.placed_rooms = placed
        self.unplaced_rooms = unplaced
        
        self.visualize_layout(placed, unplaced, f"Best Layout (Seed {seed})")
        
        # Show stats for all layouts
        stats = f"Generated 3 layouts:\n\n"
        for placed, unplaced, seed in layouts:
            stats += f"Seed {seed}: {len(placed)}/{len(self.rooms)} placed\n"
        stats += f"\nShowing best layout with {len(best_layout[0])} rooms placed."
        
        self.update_stats_text(stats)
        
    def validate_generation(self):
        """Validate before generation"""
        if not self.plot:
            messagebox.showerror("Error", "Please set plot dimensions first!")
            return False
            
        if not self.rooms:
            messagebox.showerror("Error", "Please add rooms first!")
            return False
            
        # Check feasibility
        total_room_area = sum(r.area() for r in self.rooms)
        plot_area = self.plot.area()
        
        if total_room_area > 0.7 * plot_area:
            if not messagebox.askyesno("Warning", 
                f"Total room area ({total_room_area}) exceeds 70% of plot area ({plot_area}).\n"
                "Layout may be infeasible. Continue anyway?"):
                return False
                
        return True
        
    def visualize_layout(self, placed, unplaced, title):
        """Visualize the floor plan layout"""
        self.ax.clear()
        
        if not self.plot:
            return
            
        # Set limits
        self.ax.set_xlim(0, self.plot.width)
        self.ax.set_ylim(0, self.plot.height)
        self.ax.set_aspect('equal')
        
        # Title
        unplaced_names = ", ".join([r.name for r in unplaced]) if unplaced else "None"
        self.ax.set_title(f"{title}\nPlaced: {len(placed)}/{len(self.rooms)} | Unplaced: {unplaced_names}", 
                         fontsize=10, fontweight='bold')
        
        # Draw plot boundary
        boundary = patches.Rectangle((0, 0), self.plot.width, self.plot.height,
                                     fill=False, edgecolor='black', linewidth=3)
        self.ax.add_patch(boundary)
        
        # Draw circulation space (background)
        circulation = patches.Rectangle((0, 0), self.plot.width, self.plot.height,
                                       facecolor='lightgray', alpha=0.3, label='Circulation')
        self.ax.add_patch(circulation)
        
        # Color palette
        colors = ['#a8e6cf', '#dcedc1', '#ffd3b6', '#ffaaa5', '#ff8b94', 
                 '#c7ceea', '#ffc8dd', '#bde0fe', '#a2d2ff', '#cdb4db']
        
        # Draw placed rooms
        for i, room in enumerate(placed):
            color = colors[i % len(colors)]
            rect = patches.Rectangle((room.x, room.y), room.width, room.height,
                                     facecolor=color, edgecolor='black', 
                                     linewidth=2, alpha=0.9)
            self.ax.add_patch(rect)
            
            # Room label
            self.ax.text(room.x + room.width/2, room.y + room.height/2,
                        f"{room.name}\n{room.width}×{room.height}",
                        ha='center', va='center', fontsize=8, fontweight='bold')
        
        # Legend
        if placed:
            self.ax.legend(loc='upper left', fontsize=8)
            
        self.ax.set_xlabel('Width', fontsize=9)
        self.ax.set_ylabel('Height', fontsize=9)
        
        # Add grid lines at integer positions
        self.ax.set_xticks(range(0, int(self.plot.width) + 1, 1))
        self.ax.set_yticks(range(0, int(self.plot.height) + 1, 1))
        self.ax.grid(True, which='major', alpha=0.4, linestyle='-', linewidth=0.5, color='gray')
        
        # Add minor grid lines for better precision
        self.ax.set_xticks([x + 0.5 for x in range(int(self.plot.width))], minor=True)
        self.ax.set_yticks([y + 0.5 for y in range(int(self.plot.height))], minor=True)
        self.ax.grid(True, which='minor', alpha=0.2, linestyle=':', linewidth=0.3, color='lightgray')
        
        self.canvas.draw()
        
    def clear_canvas(self):
        """Clear the visualization canvas"""
        self.ax.clear()
        self.ax.set_title("No Layout Generated", fontsize=12)
        self.ax.text(0.5, 0.5, "Configure plot and rooms, then generate layout",
                    transform=self.ax.transAxes, ha='center', va='center',
                    fontsize=10, style='italic', color='gray')
        self.ax.axis('off')
        self.canvas.draw()
        
    def update_stats(self):
        """Update statistics display"""
        if not self.plot or not self.rooms:
            stats = "Configure plot and add rooms to see statistics."
            self.update_stats_text(stats)
            return
            
        total_room_area = sum(r.area() for r in self.rooms)
        plot_area = self.plot.area()
        utilization = (total_room_area / plot_area * 100) if plot_area > 0 else 0
        
        stats = f"Plot Configuration:\n"
        stats += f"  Dimensions: {self.plot.width} × {self.plot.height}\n"
        stats += f"  Total Area: {plot_area} sq units\n\n"
        stats += f"Rooms:\n"
        stats += f"  Count: {len(self.rooms)}\n"
        stats += f"  Total Area: {total_room_area} sq units\n"
        stats += f"  Utilization: {utilization:.1f}%\n\n"
        
        if utilization > 70:
            stats += "⚠ Warning: Room area >70% of plot!\n"
            stats += "Layout may be challenging.\n"
        else:
            stats += "✓ Layout appears feasible.\n"
            
        self.update_stats_text(stats)
        
    def update_stats_after_generation(self, placed, unplaced):
        """Update statistics after generation"""
        total_room_area = sum(r.area() for r in self.rooms)
        placed_area = sum(r.width * r.height for r in placed)
        plot_area = self.plot.area()
        
        stats = f"Generation Results:\n\n"
        stats += f"Rooms Placed: {len(placed)}/{len(self.rooms)}\n"
        stats += f"Rooms Unplaced: {len(unplaced)}\n\n"
        stats += f"Areas:\n"
        stats += f"  Plot: {plot_area} sq units\n"
        stats += f"  Placed Rooms: {placed_area} sq units\n"
        stats += f"  Circulation: {plot_area - placed_area} sq units\n"
        stats += f"  Utilization: {placed_area/plot_area*100:.1f}%\n\n"
        
        if unplaced:
            stats += f"Unplaced Rooms:\n"
            for room in unplaced:
                stats += f"  • {room.name} ({room.width}×{room.height})\n"
        else:
            stats += "✓ All rooms placed successfully!\n"
            
        stats += f"\nSettings Used:\n"
        stats += f"  Corridor Width: {self.corridor_width.get()}\n"
        stats += f"  Corridor Probability: {self.corridor_prob.get():.1f}\n"
        if self.use_seed.get():
            stats += f"  Seed: {self.seed_value.get()}\n"
            
        self.update_stats_text(stats)
        
    def update_stats_text(self, text):
        """Update the stats text widget"""
        self.stats_text.config(state='normal')
        self.stats_text.delete(1.0, tk.END)
        self.stats_text.insert(1.0, text)
        self.stats_text.config(state='disabled')
        
    def save_input_file(self):
        """Save current plot and rooms configuration to JSON file"""
        if not self.plot and not self.rooms:
            messagebox.showwarning("Warning", "No data to save! Please configure plot and add rooms first.")
            return
            
        # Prepare data structure
        data = {
            "metadata": {
                "version": "1.0",
                "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "description": "Floor Plan Generator Input Configuration"
            },
            "plot": {
                "width": self.plot.width if self.plot else 0,
                "height": self.plot.height if self.plot else 0
            },
            "rooms": [
                {
                    "name": room.name,
                    "width": room._original_width,
                    "height": room._original_height
                }
                for room in self.rooms
            ],
            "settings": {
                "corridor_width": self.corridor_width.get(),
                "corridor_prob": self.corridor_prob.get(),
                "use_seed": self.use_seed.get(),
                "seed_value": self.seed_value.get() if self.use_seed.get() else None
            }
        }
        
        # Ask for file location
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")],
            title="Save Input Configuration",
            initialfile=f"floorplan_input_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        
        if not file_path:
            return
            
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            messagebox.showinfo("Success", f"Input configuration saved to:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save file:\n{str(e)}")
            
    def load_input_file(self):
        """Load plot and rooms configuration from JSON file"""
        file_path = filedialog.askopenfilename(
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")],
            title="Load Input Configuration"
        )
        
        if not file_path:
            return
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Validate data structure
            if "plot" not in data or "rooms" not in data:
                messagebox.showerror("Error", "Invalid file format! Missing required fields.")
                return
                
            # Ask for confirmation if data already exists
            if self.plot or self.rooms:
                if not messagebox.askyesno("Confirm", 
                    "This will replace current configuration. Continue?"):
                    return
                    
            # Clear existing data
            self.rooms.clear()
            self.rooms_listbox.delete(0, tk.END)
            self.plot = None
            
            # Load plot configuration
            plot_data = data["plot"]
            self.plot_width_entry.delete(0, tk.END)
            self.plot_width_entry.insert(0, str(plot_data["width"]))
            self.plot_height_entry.delete(0, tk.END)
            self.plot_height_entry.insert(0, str(plot_data["height"]))
            
            if plot_data["width"] > 0 and plot_data["height"] > 0:
                self.plot = Plot(plot_data["width"], plot_data["height"])
                
            # Load rooms
            for room_data in data["rooms"]:
                room = Room(room_data["width"], room_data["height"], room_data["name"])
                self.rooms.append(room)
                self.rooms_listbox.insert(tk.END, 
                    f"{room_data['name']} ({room_data['width']}x{room_data['height']})")
                    
            # Load settings if available
            if "settings" in data:
                settings = data["settings"]
                self.corridor_width.set(settings.get("corridor_width", 3))
                self.corridor_prob.set(settings.get("corridor_prob", 0.3))
                self.use_seed.set(settings.get("use_seed", False))
                if settings.get("seed_value") is not None:
                    self.seed_value.set(settings["seed_value"])
                self.toggle_seed()
                
            self.update_stats()
            messagebox.showinfo("Success", 
                f"Loaded configuration:\n• Plot: {plot_data['width']}×{plot_data['height']}\n• Rooms: {len(self.rooms)}")
                
        except json.JSONDecodeError:
            messagebox.showerror("Error", "Invalid JSON file format!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file:\n{str(e)}")


def main():
    root = tk.Tk()
    app = GeneratorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
