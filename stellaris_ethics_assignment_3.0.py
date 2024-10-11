import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import itertools
import pulp  # ILP library

# Define the ethics with their options and costs
ethics = [
    {'name': 'Materialist', 'options': ['None', 'Normal', 'Fanatic'], 'costs': {'None': 0, 'Normal': 1, 'Fanatic': 2}},
    {'name': 'Spiritualist', 'options': ['None', 'Normal', 'Fanatic'], 'costs': {'None': 0, 'Normal': 1, 'Fanatic': 2}},
    {'name': 'Xenophile', 'options': ['None', 'Normal', 'Fanatic'], 'costs': {'None': 0, 'Normal': 1, 'Fanatic': 2}},
    {'name': 'Xenophobe', 'options': ['None', 'Normal', 'Fanatic'], 'costs': {'None': 0, 'Normal': 1, 'Fanatic': 2}},
    {'name': 'Egalitarian', 'options': ['None', 'Normal', 'Fanatic'], 'costs': {'None': 0, 'Normal': 1, 'Fanatic': 2}},
    {'name': 'Authoritarian', 'options': ['None', 'Normal', 'Fanatic'], 'costs': {'None': 0, 'Normal': 1, 'Fanatic': 2}},
    {'name': 'Pacifist', 'options': ['None', 'Normal', 'Fanatic'], 'costs': {'None': 0, 'Normal': 1, 'Fanatic': 2}},
    {'name': 'Militarist', 'options': ['None', 'Normal', 'Fanatic'], 'costs': {'None': 0, 'Normal': 1, 'Fanatic': 2}},
    {'name': 'Gestalt Consciousness', 'options': ['None', 'Gestalt'], 'costs': {'None': 0, 'Gestalt': 3}}
]

# Define conflicting ethics pairs
conflicts = [
    ('Materialist', 'Spiritualist'),
    ('Fanatic Materialist', 'Spiritualist'),
    ('Materialist', 'Fanatic Spiritualist'),
    ('Fanatic Materialist', 'Fanatic Spiritualist'),
    ('Xenophile', 'Xenophobe'),
    ('Fanatic Xenophile', 'Xenophobe'),
    ('Xenophile', 'Fanatic Xenophobe'),
    ('Fanatic Xenophile', 'Fanatic Xenophobe'),
    ('Egalitarian', 'Authoritarian'),
    ('Fanatic Egalitarian', 'Authoritarian'),
    ('Egalitarian', 'Fanatic Authoritarian'),
    ('Fanatic Egalitarian', 'Fanatic Authoritarian'),
    ('Pacifist', 'Militarist'),
    ('Fanatic Pacifist', 'Militarist'),
    ('Pacifist', 'Fanatic Militarist'),
    ('Fanatic Pacifist', 'Fanatic Militarist'),
    # Gestalt conflicts with all other ethics
]

# Initialize the main window
root = tk.Tk()
root.title("Stellaris Ethics Assignment")

# Create a canvas and a scrollbar for the entire application
main_canvas = tk.Canvas(root)
main_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

main_scrollbar = ttk.Scrollbar(root, orient='vertical', command=main_canvas.yview)
main_scrollbar.pack(side=tk.RIGHT, fill='y')

main_canvas.configure(yscrollcommand=main_scrollbar.set)

# Create a frame inside the canvas to hold all the widgets
main_frame = ttk.Frame(main_canvas)
main_canvas.create_window((0, 0), window=main_frame, anchor='nw')

# Ensure the scroll region is updated when the main_frame is resized
def on_main_frame_configure(event):
    main_canvas.configure(scrollregion=main_canvas.bbox('all'))
    # Update the width of main_frame to match the canvas width
    canvas_width = main_canvas.winfo_width()
    main_canvas.itemconfig(main_frame_window, width=canvas_width)

main_frame.bind('<Configure>', on_main_frame_configure)

# Bind mouse wheel scrolling to the canvas
def _on_mousewheel(event):
    main_canvas.yview_scroll(int(-1*(event.delta/120)), "units")

main_canvas.bind_all("<MouseWheel>", _on_mousewheel)

# Initialize players list
players = []

# Dictionary to hold the ethic selections for each player
player_ethics_vars = {}  # Key: (player, ethic), Value: StringVar

# Dictionary to hold submission status for each player
player_submitted_vars = {}  # Key: player, Value: BooleanVar

# Dictionary to hold player frames for easy removal
player_frames = {}

# Variables to hold counts labels
counts_labels = {}

# Function to add a new player
def add_player():
    player_name = player_name_entry.get().strip()
    if not player_name:
        messagebox.showerror("Error", "Player name cannot be empty.")
        return
    if player_name in players:
        messagebox.showerror("Error", "Player name must be unique.")
        return
    players.append(player_name)
    # Initialize ethics selections
    for ethic in ethics:
        player_ethics_vars[(player_name, ethic['name'])] = tk.StringVar(value='None')
    # Initialize submission status
    player_submitted_vars[player_name] = tk.BooleanVar(value=False)
    # Add trace to the submission status variable
    player_submitted_vars[player_name].trace_add('write', lambda *args, p=player_name: live_update(p))
    player_name_entry.delete(0, tk.END)
    update_gui()

# Function to remove a player
def remove_player(player_name):
    if player_name in players:
        # Remove player's variables
        for ethic in ethics:
            player_ethics_vars.pop((player_name, ethic['name']), None)
        # Remove submission status
        player_submitted_vars.pop(player_name, None)
        players.remove(player_name)
        # Remove player's frame
        frame = player_frames.pop(player_name, None)
        if frame:
            frame.destroy()
        update_gui()

# Function to edit a player's name
def edit_player_name(player_name):
    # Get the frame for the player
    frame = player_frames[player_name]
    header_frame = frame.winfo_children()[0]
    # Replace the name label with an Entry widget
    name_label = header_frame.winfo_children()[1]  # Adjusted index due to checkbox
    name_label.destroy()
    name_entry = ttk.Entry(header_frame)
    name_entry.insert(0, player_name)
    name_entry.pack(side='left', padx=(5, 0))
    # Replace the Edit button with a Save button
    edit_button = header_frame.winfo_children()[2]
    edit_button.destroy()
    save_button = ttk.Button(header_frame, text="Save", command=lambda: save_player_name(player_name, name_entry.get()))
    save_button.pack(side='right')
    # Keep the remove button
    # Remove button remains as the last child

# Function to save the new player name
def save_player_name(old_name, new_name):
    new_name = new_name.strip()
    if not new_name:
        messagebox.showerror("Error", "Player name cannot be empty.")
        return
    if new_name in players and new_name != old_name:
        messagebox.showerror("Error", "Player name must be unique.")
        return
    # Update the players list
    index = players.index(old_name)
    players[index] = new_name
    # Update player_ethics_vars
    for key in list(player_ethics_vars.keys()):
        if key[0] == old_name:
            player_ethics_vars[(new_name, key[1])] = player_ethics_vars.pop(key)
    # Update player_submitted_vars
    player_submitted_vars[new_name] = player_submitted_vars.pop(old_name)
    # Update player_frames
    frame = player_frames.pop(old_name)
    player_frames[new_name] = frame
    # Update the GUI
    update_gui()

# Function to create an option menu with dynamic color change
def create_option_menu(var, options, frame, row, col):
    option_menu = tk.OptionMenu(frame, var, *options)
    option_menu.config(width=12)
    option_menu.grid(row=row, column=col, padx=2, pady=2)
    option_menu.grid_configure(sticky='ew')

    def update_option_menu_color(*args):
        selection = var.get()
        if selection == 'None':
            option_menu.config(bg='grey')
        else:
            option_menu.config(bg='lightblue')

    # Initial color update
    update_option_menu_color()

    # Trace variable changes
    var.trace_add('write', update_option_menu_color)

    return option_menu

# Function to update the GUI with the current players
def update_gui():
    # Clear previous widgets in player_list_frame
    for widget in player_list_frame.winfo_children():
        widget.destroy()
    player_frames.clear()
    # Create player frames with numbering
    for idx, player in enumerate(players, start=1):
        frame = ttk.Frame(player_list_frame, relief='solid', borderwidth=1, padding=5)
        frame.grid(row=idx-1, column=0, pady=5, sticky='ew')
        frame.grid_columnconfigure(0, weight=1)
        player_frames[player] = frame
        # Player header with numbering and checkbox
        header_frame = ttk.Frame(frame)
        header_frame.pack(fill='x')
        # Checkbox for submission status
        submitted_cb = ttk.Checkbutton(header_frame, variable=player_submitted_vars[player])
        submitted_cb.pack(side='left')
        # Player name with numbering
        name_label = ttk.Label(header_frame, text=f"{idx}. {player}", font=('Arial', 12, 'bold'))
        name_label.pack(side='left', padx=(5, 0))
        # Edit and Remove buttons
        edit_button = ttk.Button(header_frame, text="Edit", command=lambda p=player: edit_player_name(p))
        edit_button.pack(side='right')
        remove_button = ttk.Button(header_frame, text="Remove", command=lambda p=player: remove_player(p))
        remove_button.pack(side='right')
        # Ethics selection frame
        ethics_frame = ttk.Frame(frame)
        ethics_frame.pack(fill='x', pady=5)
        ethics_frame.grid_columnconfigure(tuple(range(len(ethics))), weight=1)
        # Add labels and option menus in a grid
        for col, ethic in enumerate(ethics):
            # Add label in row 0
            ttk.Label(ethics_frame, text=ethic['name']).grid(row=0, column=col, padx=2, pady=2, sticky='ew')
            # Add option menu in row 1
            var = player_ethics_vars.get((player, ethic['name']))
            if var is None:
                var = tk.StringVar(value='None')
                player_ethics_vars[(player, ethic['name'])] = var
            options = ethic['options']
            # Create the option menu with dynamic color change
            option_menu = create_option_menu(var, options, ethics_frame, 1, col)
            # Bind live update to changes
            var.trace_add('write', lambda *args, p=player: live_update(p))
    # Update the live assignments table and validation messages
    validate_assignments()
    update_assignments_table()
    update_counts_table()
    update_groupings()

# Function to perform live updates and validations
def live_update(changed_player=None):
    # Perform validation and update assignments
    validate_assignments()
    update_assignments_table()
    update_counts_table()
    update_groupings()

# Function to validate assignments
def validate_assignments():
    global validation_errors
    validation_errors = []
    combination_counts = {}
    combinations_per_player = {}
    for player in players:
        total_cost = 0
        selected_ethic_names = []
        selected_ethics_set = set()
        gestalt_selected = False
        for ethic in ethics:
            selection = player_ethics_vars[(player, ethic['name'])].get()
            cost = ethic['costs'].get(selection, 0)
            total_cost += cost
            if selection != 'None':
                if selection == 'Gestalt':
                    selected_ethic_names.append('Gestalt Consciousness')
                    selected_ethics_set.add('Gestalt Consciousness')
                    gestalt_selected = True
                else:
                    ethic_name = f"{selection} {ethic['name']}" if selection == 'Fanatic' else ethic['name']
                    selected_ethic_names.append(ethic_name)
                    selected_ethics_set.add(ethic_name)
        # Check for total cost not equal to 3
        if total_cost != 3:
            validation_errors.append(f"{player}: Total points spent is {total_cost}, should be exactly 3.")
        # Check for conflicting ethics
        if gestalt_selected and len(selected_ethic_names) > 1:
            validation_errors.append(f"{player}: Gestalt Consciousness cannot be combined with other ethics.")
        for conflict_pair in conflicts:
            if conflict_pair[0] in selected_ethics_set and conflict_pair[1] in selected_ethics_set:
                validation_errors.append(f"{player}: Conflicting ethics selected - {conflict_pair[0]} and {conflict_pair[1]}.")
        # Prepare for duplicate checking
        combination = tuple(sorted(selected_ethic_names))
        combinations_per_player[player] = combination
        if total_cost == 3:
            # Exclude Gestalt-only combinations from duplicate checks
            if not (len(combination) == 1 and 'Gestalt Consciousness' in combination):
                combination_counts[combination] = combination_counts.get(combination, 0) + 1
    # Check for duplicates
    duplicates = [comb for comb, count in combination_counts.items() if count > 1]
    duplicate_players = {}
    for player, comb in combinations_per_player.items():
        if comb in duplicates:
            if comb not in duplicate_players:
                duplicate_players[comb] = []
            duplicate_players[comb].append(player)
    # Update the validation messages
    messages = []
    if duplicates:
        for comb, players_with_comb in duplicate_players.items():
            messages.append(f"Duplicate combination {', '.join(comb)} found for players: {', '.join(players_with_comb)}.")
    else:
        messages.append("All ethic combinations are unique.")
    if validation_errors:
        messages.append("Validation Errors:")
        messages.extend(validation_errors)
    else:
        messages.append("All player assignments are valid.")
    validation_label.config(text="\n".join(messages), foreground="red" if validation_errors or duplicates else "green")

# Function to update the live assignments table with numeration and submission status
def update_assignments_table():
    # Clear previous assignments
    for item in assignments_tree.get_children():
        assignments_tree.delete(item)
    # Create new assignments with numbering and submission status
    for idx, player in enumerate(players, start=1):
        selected_ethic_names = []
        total_cost = 0
        for ethic in ethics:
            selection = player_ethics_vars[(player, ethic['name'])].get()
            cost = ethic['costs'].get(selection, 0)
            total_cost += cost
            if selection != 'None':
                if selection == 'Gestalt':
                    selected_ethic_names.append('Gestalt Consciousness')
                else:
                    ethic_name = f"{selection} {ethic['name']}" if selection == 'Fanatic' else ethic['name']
                    selected_ethic_names.append(ethic_name)
        ethics_text = ', '.join(selected_ethic_names)
        # Get submission status
        submitted = "Yes" if player_submitted_vars[player].get() else "No"
        # Determine the tag based on submission status
        tag = 'submitted_yes' if submitted == "Yes" else 'submitted_no'
        assignments_tree.insert('', 'end', values=(idx, player, ethics_text, total_cost, submitted), tags=(tag,))
    # Configure tags for coloring
    assignments_tree.tag_configure('submitted_yes', background='lightgreen')
    assignments_tree.tag_configure('submitted_no', background='lightcoral')

# Function to update the ethics counts display
def update_counts_table():
    # Clear previous counts labels
    for label in counts_labels.values():
        label.destroy()
    counts_labels.clear()
    # Initialize counts dictionary
    counts = {}
    for ethic in ethics:
        if ethic['name'] != 'Gestalt Consciousness':
            counts[ethic['name']] = 0  # Normal
            counts[f"Fanatic {ethic['name']}"] = 0  # Fanatic
        else:
            counts['Gestalt Consciousness'] = 0

    # Accumulate counts
    for player in players:
        for ethic in ethics:
            selection = player_ethics_vars[(player, ethic['name'])].get()
            if selection == 'Normal':
                counts[ethic['name']] += 1
            elif selection == 'Fanatic':
                counts[f"Fanatic {ethic['name']}"] += 1
            elif selection == 'Gestalt':
                counts['Gestalt Consciousness'] += 1
            # else: selection is 'None', do nothing

    # Prepare to collect warnings and label colours
    counts_labels_colours = {}  # Key: ethic name, Value: colour (e.g., 'red')
    ethic_warnings = []  # List of messages

    # List of opposing pairs for normal ethics
    opposing_ethics = [
        ('Materialist', 'Spiritualist'),
        ('Xenophile', 'Xenophobe'),
        ('Egalitarian', 'Authoritarian'),
        ('Pacifist', 'Militarist'),
    ]

    # Compare counts for opposing ethics
    for ethic1, ethic2 in opposing_ethics:
        count1 = counts[ethic1]
        count2 = counts[ethic2]
        if count1 > count2:
            counts_labels_colours[ethic1] = 'red'
            ethic_warnings.append(f"{ethic1} has more assignments than {ethic2}.")
        elif count2 > count1:
            counts_labels_colours[ethic2] = 'red'
            ethic_warnings.append(f"{ethic2} has more assignments than {ethic1}.")

    # Arrange counts in two columns
    row = 0
    col = 0
    for ethic_display_name in counts.keys():
        count = counts[ethic_display_name]
        fg_color = counts_labels_colours.get(ethic_display_name, 'black')
        label = ttk.Label(counts_frame, text=f"{ethic_display_name}: {count}", foreground=fg_color)
        label.grid(row=row, column=col, sticky='w', padx=5, pady=2)
        counts_labels[ethic_display_name] = label
        if col == 1:
            col = 0
            row += 1
        else:
            col += 1

    # Update counts warning label
    if ethic_warnings:
        counts_warning_label.config(text='\n'.join(ethic_warnings), foreground='red')
    else:
        counts_warning_label.config(text='')

# Function to update groupings using ILP for optimal grouping
def update_groupings():
    # Build conflict graph between players excluding those with Gestalt Consciousness
    player_ethics = {}
    players_to_group = []
    for player in players:
        selected_ethics = set()
        has_gestalt = False
        for ethic in ethics:
            selection = player_ethics_vars[(player, ethic['name'])].get()
            if selection == 'Gestalt':
                has_gestalt = True
                break  # Skip this player for groupings
            if selection != 'None':
                if selection == 'Fanatic':
                    ethic_name = f"Fanatic {ethic['name']}"
                else:
                    ethic_name = ethic['name']
                selected_ethics.add(ethic_name)
        if not has_gestalt:
            players_to_group.append(player)
            player_ethics[player] = selected_ethics

    # Create conflict graph
    conflict_graph = {}
    for player in players_to_group:
        conflict_graph[player] = set()

    for i in range(len(players_to_group)):
        for j in range(i+1, len(players_to_group)):
            player1 = players_to_group[i]
            player2 = players_to_group[j]
            ethics1 = player_ethics[player1]
            ethics2 = player_ethics[player2]
            # Check for conflicts between player1 and player2
            conflict_found = False
            for conflict_pair in conflicts:
                if (conflict_pair[0] in ethics1 and conflict_pair[1] in ethics2) or \
                   (conflict_pair[1] in ethics1 and conflict_pair[0] in ethics2):
                    conflict_found = True
                    break
            if conflict_found:
                conflict_graph[player1].add(player2)
                conflict_graph[player2].add(player1)

    # If no players to group, clear groupings
    if not players_to_group:
        groups = []
    else:
        # Initialize ILP problem
        prob = pulp.LpProblem("Optimal_Grouping", pulp.LpMinimize)

        # Variables
        # Assuming maximum groups equal to number of players
        max_groups = len(players_to_group)
        group_indices = list(range(max_groups))
        x = pulp.LpVariable.dicts("assign",
                                  ((player, group) for player in players_to_group for group in group_indices),
                                  cat='Binary')
        y = pulp.LpVariable.dicts("use_group",
                                  (group for group in group_indices),
                                  cat='Binary')

        # Objective: Minimize the number of groups used
        prob += pulp.lpSum([y[group] for group in group_indices])

        # Constraints:

        # 1. Each player must be assigned to exactly one group
        for player in players_to_group:
            prob += pulp.lpSum([x[(player, group)] for group in group_indices]) == 1, f"OneGroup_{player}"

        # 2. If a player is assigned to a group, that group must be used
        for player in players_to_group:
            for group in group_indices:
                prob += x[(player, group)] <= y[group], f"UseGroup_{player}_{group}"

        # 3. No group can have more than 6 players
        for group in group_indices:
            prob += pulp.lpSum([x[(player, group)] for player in players_to_group]) <= 6, f"MaxSize_Group_{group}"

        # 4. Conflicting players cannot be in the same group
        for group in group_indices:
            for player1, player2 in itertools.combinations(players_to_group, 2):
                if player2 in conflict_graph[player1]:
                    prob += x[(player1, group)] + x[(player2, group)] <= 1, f"NoConflict_{player1}_{player2}_Group_{group}"

        # Solve the problem
        solver = pulp.PULP_CBC_CMD(msg=False)  # msg=True for solver output
        prob.solve(solver)

        # Check if a valid solution was found
        if pulp.LpStatus[prob.status] != 'Optimal':
            messagebox.showerror("Error", "Failed to find an optimal grouping. Please check the assignments.")
            groups = []
        else:
            # Extract group assignments
            groups = []
            for group in group_indices:
                if pulp.value(y[group]) == 1:
                    group_members = [player for player in players_to_group if pulp.value(x[(player, group)]) == 1]
                    if group_members:
                        groups.append(group_members)

    # Clear previous groupings
    for widget in groupings_frame.winfo_children():
        widget.destroy()

    # Display groupings with numbering
    ttk.Label(groupings_frame, text=f"Total Groupings: {len(groups)}", font=('Arial', 12, 'bold')).grid(row=0, column=0, sticky='w', pady=5)
    row = 1
    if groups:
        for idx, group in enumerate(groups, start=1):
            group_label = ttk.Label(groupings_frame, text=f"Group {idx}: {', '.join(group)}")
            group_label.grid(row=row, column=0, sticky='w')
            row += 1
    else:
        ttk.Label(groupings_frame, text="No groupings available.", font=('Arial', 10)).grid(row=row, column=0, sticky='w')
        row += 1

    # List players excluded from groupings (those with Gestalt Consciousness)
    gestalt_players = [player for player in players if player not in players_to_group]
    if gestalt_players:
        ttk.Label(groupings_frame, text="Players excluded from groupings (Gestalt Consciousness):", font=('Arial', 12, 'bold')).grid(row=row, column=0, sticky='w', pady=5)
        row += 1
        ttk.Label(groupings_frame, text=', '.join(gestalt_players)).grid(row=row, column=0, sticky='w')
        row += 1

# Function to export assignments to Excel
def export_assignments():
    assignments = []
    for player in players:
        assignment = {'Player': player}
        total_cost = 0
        for ethic in ethics:
            selection = player_ethics_vars[(player, ethic['name'])].get()
            assignment[ethic['name']] = selection
            cost = ethic['costs'].get(selection, 0)
            total_cost += cost
        assignment['Total Cost'] = total_cost
        # Add submission status
        assignment['Submitted'] = "Yes" if player_submitted_vars[player].get() else "No"
        assignments.append(assignment)
    df = pd.DataFrame(assignments)
    save_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx *.xls")])
    if save_path:
        try:
            # Check if openpyxl is installed
            import openpyxl
            df.to_excel(save_path, index=False)
            messagebox.showinfo("Success", f"Assignments exported successfully to {save_path}.")
        except ImportError:
            messagebox.showerror("Error", "The 'openpyxl' module is required to export to Excel. Please install it using 'pip install openpyxl'.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export assignments: {e}")

# Function to import assignments from Excel
def import_assignments():
    file_path = filedialog.askopenfilename(title="Select Excel File", filetypes=[("Excel files", "*.xlsx *.xls")])
    if not file_path:
        return
    try:
        df = pd.read_excel(file_path)
        # Check if 'Submitted' column exists
        submitted_exists = 'Submitted' in df.columns
        # Clear current data
        players.clear()
        player_ethics_vars.clear()
        player_submitted_vars.clear()
        # Load data
        for index, row in df.iterrows():
            player_name = str(row['Player'])
            if player_name in players:
                messagebox.showerror("Error", f"Duplicate player name '{player_name}' in the imported file.")
                return
            players.append(player_name)
            for ethic in ethics:
                selection = row.get(ethic['name'], 'None')
                if pd.isna(selection):
                    selection = 'None'
                player_ethics_vars[(player_name, ethic['name'])] = tk.StringVar(value=selection)
            # Set submission status
            if submitted_exists:
                submitted = row.get('Submitted', 'No')
                if isinstance(submitted, str):
                    submitted = submitted.strip().lower() == 'yes'
                else:
                    submitted = bool(submitted)
            else:
                submitted = False  # Default to 'No' if 'Submitted' column is missing
            player_submitted_vars[player_name] = tk.BooleanVar(value=submitted)
            # Add trace to the submission status variable
            player_submitted_vars[player_name].trace_add('write', lambda *args, p=player_name: live_update(p))
        update_gui()
        messagebox.showinfo("Success", "Assignments imported successfully.")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to import assignments: {e}")

# Create the GUI components inside main_frame
main_frame.grid_columnconfigure(0, weight=1)

# Top frame (Add Player)
top_frame = ttk.Frame(main_frame)
top_frame.grid(row=0, column=0, pady=10)
top_frame.grid_columnconfigure(0, weight=1)

player_name_label = ttk.Label(top_frame, text="Player Name:")
player_name_label.pack(side=tk.LEFT, padx=5)

player_name_entry = ttk.Entry(top_frame)
player_name_entry.pack(side=tk.LEFT, padx=5)

add_player_button = ttk.Button(top_frame, text="Add Player", command=add_player)
add_player_button.pack(side=tk.LEFT, padx=5)

import_button = ttk.Button(top_frame, text="Load from Excel", command=import_assignments)
import_button.pack(side=tk.LEFT, padx=5)

# Counts frame
counts_frame = ttk.Frame(main_frame)
counts_frame.grid(row=1, column=0, pady=10, sticky='ew')
counts_frame.grid_columnconfigure(0, weight=1)

# Add counts warning label below counts_frame
counts_warning_label = ttk.Label(main_frame, text='', foreground='red')
counts_warning_label.grid(row=2, column=0, pady=5, sticky='ew')

# Initialize counts display
update_counts_table()

# Create a frame for the player list
player_list_frame = ttk.Frame(main_frame)
player_list_frame.grid(row=3, column=0, pady=10, sticky='ew')
player_list_frame.grid_columnconfigure(0, weight=1)

# Create the groupings display
groupings_frame = ttk.Frame(main_frame)
groupings_frame.grid(row=4, column=0, pady=10, sticky='ew')
groupings_frame.grid_columnconfigure(0, weight=1)

# Initialize groupings display
update_groupings()

# Create the assignments table with scrollbar and numeration
assignments_frame = ttk.Frame(main_frame)
assignments_frame.grid(row=5, column=0, pady=10, sticky='ew')
assignments_frame.grid_columnconfigure(0, weight=1)

assignments_scrollbar = ttk.Scrollbar(assignments_frame, orient='vertical')
assignments_scrollbar.pack(side='right', fill='y')

# Add a "Submitted" column for checkbox status
assignments_tree = ttk.Treeview(assignments_frame, columns=('No.', 'Player', 'Ethics', 'Total Cost', 'Submitted'), show='headings', yscrollcommand=assignments_scrollbar.set)
assignments_tree.heading('No.', text='No.')
assignments_tree.heading('Player', text='Player')
assignments_tree.heading('Ethics', text='Ethics')
assignments_tree.heading('Total Cost', text='Total Cost')
assignments_tree.heading('Submitted', text='Submitted')
assignments_tree.column('No.', width=50, anchor='center')  # Adjusted width for numbering
assignments_tree.column('Player', width=150, anchor='center')
assignments_tree.column('Ethics', width=400, anchor='center')
assignments_tree.column('Total Cost', width=100, anchor='center')
assignments_tree.column('Submitted', width=100, anchor='center')  # Adjusted width for submission status
assignments_tree.pack(side='left', fill='both', expand=True)

assignments_scrollbar.config(command=assignments_tree.yview)

# Define tags for coloring rows based on "Submitted" status
assignments_tree.tag_configure('submitted_yes', background='lightgreen')
assignments_tree.tag_configure('submitted_no', background='lightcoral')

# Validation message area
validation_label = ttk.Label(main_frame, text="", foreground="green")
validation_label.grid(row=6, column=0, pady=5, sticky='ew')

# Initialize validation messages
validate_assignments()

# Buttons frame
buttons_frame = ttk.Frame(main_frame)
buttons_frame.grid(row=7, column=0, pady=5)

# Export button
export_button = ttk.Button(buttons_frame, text="Export to Excel", command=export_assignments)
export_button.pack(padx=5)

# Update the canvas window item configuration
main_frame_window = main_canvas.create_window((0, 0), window=main_frame, anchor='nw')

# Start the GUI loop
root.mainloop()
