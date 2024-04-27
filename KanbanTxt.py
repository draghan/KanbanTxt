# KanbanTxt - A light todo.txt editor that display the to do list as a kanban board.
# Copyright (C) 2022  KrisNumber24

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  
# If not, see https://github.com/KrisNumber24/KanbanTxt/blob/main/LICENSE.

import os
import pathlib
import re
from datetime import date
import tkinter as tk
from tkinter import filedialog
import tkinter.font as tkFont
import argparse
from idlelib.tooltip import Hovertip
import ctypes

class KanbanTxtViewer:
    COLUMN_NAME_TODO = "To Do"
    COLUMN_NAME_IN_PROGRESS = "In progress"
    COLUMN_NAME_VALIDATION = "Validation"
    COLUMN_NAME_DONE = "Done"

    COLUMNS_NAMES = [
        COLUMN_NAME_TODO,
        COLUMN_NAME_IN_PROGRESS,
        COLUMN_NAME_VALIDATION,
        COLUMN_NAME_DONE
    ]

    THEMES = {
        'LIGHT_COLORS': {
            COLUMN_NAME_TODO: '#f27272',
            COLUMN_NAME_IN_PROGRESS: '#00b6e4',
            COLUMN_NAME_VALIDATION: '#22b57f',
            COLUMN_NAME_DONE: "#8BC34A",
            f"{COLUMN_NAME_TODO}-column": '#daecf1',
            f"{COLUMN_NAME_IN_PROGRESS}-column": '#daecf1',
            f"{COLUMN_NAME_VALIDATION}-column": '#daecf1',
            f"{COLUMN_NAME_DONE}-column": "#daecf1",
            "important": "#a7083b",
            "project": '#00b6e4',
            'context': '#1c9c6d',
            'main-background': "#C0D6E8",
            'card-background': '#ffffff',
            'done-card-background': '#edf5f7',
            'editor-background': '#cae1e8',
            'main-text': '#4c6066',
            'editor-text': '#000000',
            'button': '#415358',
            'kv-data': '#b8becc',
            'priority_color_scale': [
                "#ec1c24",
                "#ff7f27",
                "#ffca18",
                "#77dd77",
                "#aec6cf"
            ]
        },

        'DARK_COLORS': {
            COLUMN_NAME_TODO: '#f27272',
            COLUMN_NAME_IN_PROGRESS: '#00b6e4',
            COLUMN_NAME_VALIDATION: '#22b57f',
            COLUMN_NAME_DONE: "#8BC34A",
            f"{COLUMN_NAME_TODO}-column": '#15151f',
            f"{COLUMN_NAME_IN_PROGRESS}-column": '#15151f',
            f"{COLUMN_NAME_VALIDATION}-column": '#15151f',
            f"{COLUMN_NAME_DONE}-column": "#15151f",
            "important": "#e12360",
            "project": '#00b6e4',
            'context': '#1c9c6d',
            'main-background': "#1f1f2b",
            'card-background': '#2c2c3a',
            'done-card-background': '#1f1f2b',
            'editor-background': '#15151f',
            'main-text': '#b6cbd1',
            'editor-text': '#cee4eb',
            'button': '#b6cbd1',
            'kv-data': '#43454a',
            'priority_color_scale': [
                "#ff6961",
                "#ffb347",
                "#fdfd96",
                "#77dd77",
                "#aec6cf"
            ]
        },
    }

    FONTS = []

    KANBAN_KEY = "knbn"

    KANBAN_VAL_IN_PROGRESS = "in_progress"

    KANBAN_VAL_VALIDATION = "validation"

    def __init__(self, file='', darkmode=False) -> None:
        self.drag_begin_cursor_pos = (0, 0)
        self.dragged_widgets = []
        self.drop_areas = []
        self.drop_areas_frame = None
        self.darkmode = darkmode

        self.file = file

        self.current_date = date.today()

        self.ui_columns = {}
        for col in self.COLUMNS_NAMES:
            self.ui_columns[col] = []

        self._after_id = -1

        self.selected_task_card = None

        self.draw_ui(1000, 700, 0, 0)

    def draw_ui(self, window_width, window_height, window_x, window_y):
        # Define theme
        dark_option = 'LIGHT_COLORS'
        if self.darkmode: 
            dark_option = 'DARK_COLORS'

        default_scheme = list(self.THEMES.keys())[0]
        color_scheme = self.THEMES.get(dark_option, default_scheme)

        self.COLORS = color_scheme

        # Create main window
        self.main_window = tk.Tk()
        self.main_window.bind('<Button-1>', self.clear_drop_areas_frame)
        self.main_window.title('KanbanTxt')
        icon_path = pathlib.Path('icons8-kanban-64.png')
        if icon_path.exists():
            self.main_window.iconphoto(False, tk.PhotoImage(file=icon_path))

        self.main_window['background'] = self.COLORS['main-background']
        self.main_window['relief'] = 'flat'
        self.main_window.geometry("%dx%d+%d+%d" % (window_width, window_height, window_x, window_y))

        self.FONTS.append(tkFont.Font(name='main', family='arial', size=10, weight=tkFont.NORMAL))
        self.FONTS.append(tkFont.Font(name='h2', family='arial', size=14, weight=tkFont.NORMAL))
        self.FONTS.append(tkFont.Font(name='done-task', family='arial', size='10', overstrike=1))

        # Bind shortkey to open or save a new file
        self.main_window.bind('<Control-s>', self.reload_and_create_file)
        self.main_window.bind('<Control-o>', self.open_file)

        self.draw_editor_panel()

        self.draw_content_frame()

        # Load the file provided in arguments if there is one
        if os.path.isfile(self.file):
            self.load_file()

    def get_cursor_pos(self):
        return self.main_window.winfo_pointerx(), self.main_window.winfo_pointery()

    def clear_drop_areas_frame(self, event=None):
        if self.drop_areas_frame is not None:
            self.drop_areas_frame.destroy()
            self.drop_areas_frame = None

    def on_click(self, event):
        self.drag_begin_cursor_pos = self.get_cursor_pos()
        self.highlight_task(event)

    def on_drag_init(self, event):
        dragged_widget_name = event.widget.winfo_name()
        if dragged_widget_name in self.dragged_widgets:
            return
        self.clear_drop_areas_frame()
        self.dragged_widgets.append(dragged_widget_name)
        self.main_window.after(50, self.on_drag, event) # a little delay to give the UI time to refresh highlighted task card

    def on_drag(self, event):
        event.widget.config(cursor="fleur")

        # properties of a single drop area
        drop_area_width = 100
        drop_area_height = 100
        drop_area_spacing = 25

        # properties of the parent window for drop areas
        # should appear above currently dragged task card, and it should not protrude beyond
        # the border of the main window
        drop_areas_frame_border = 4
        drop_areas_title_text_pos_y = 10
        drop_areas_pos_x = drop_area_spacing
        drop_areas_pos_y = 2 * drop_areas_title_text_pos_y

        self.drop_areas.clear()
        # determine whether user dragged vertically (to change priority) or horizontally (to change column)
        cursor_x_pos, cursor_y_pos = self.get_cursor_pos()
        distance_x = abs(cursor_x_pos - self.drag_begin_cursor_pos[0])
        distance_y = abs(cursor_y_pos - self.drag_begin_cursor_pos[1])
        if distance_x >= distance_y:
            drop_areas_title = "Move this task to:"
            move_functors = {
                self.COLUMN_NAME_TODO: self.move_to_todo,
                self.COLUMN_NAME_IN_PROGRESS: self.move_to_in_progress,
                self.COLUMN_NAME_VALIDATION: self.move_to_validation,
                self.COLUMN_NAME_DONE: self.move_to_done,
            }
            for column_name in self.COLUMNS_NAMES:
                self.drop_areas.append({
                    'name': column_name,
                    'color': self.COLORS[column_name],
                    'functor': move_functors[column_name],
                    'x1': drop_areas_pos_x,
                    'y1': drop_areas_pos_y,
                    'x2': drop_areas_pos_x + drop_area_width,
                    'y2': drop_areas_pos_y + drop_area_height
                })
                drop_areas_pos_x += drop_area_spacing + drop_area_width
        else:
            drop_areas_title = "Change priority to:"
            priority_functors = {
                "A": self.change_priority_to_A,
                "B": self.change_priority_to_B,
                "C": self.change_priority_to_C,
                "D": self.change_priority_to_D,
                "E": self.change_priority_to_E,
                "(none)": lambda: self.change_priority(None, "")
            }
            i = 0
            for priority in priority_functors.keys():
                color = 'white'
                if i < len(self.COLORS['priority_color_scale']):
                    color = self.COLORS['priority_color_scale'][i]
                i += 1
                self.drop_areas.append({
                    'name': priority,
                    'color': color,
                    'functor': priority_functors[priority],
                    'x1': drop_areas_pos_x,
                    'y1': drop_areas_pos_y,
                    'x2': drop_areas_pos_x + drop_area_width,
                    'y2': drop_areas_pos_y + drop_area_height
                })
                drop_areas_pos_x += drop_area_spacing + drop_area_width

        task_card_frame_widget = self.get_task_card_frame_widget(event.widget)
        drop_areas_frame_width = (drop_area_width + drop_area_spacing) * (len(self.drop_areas) + 1)
        drop_areas_frame_pos_x = cursor_x_pos - int(drop_areas_frame_width / 2)
        drop_areas_frame_pos_y = task_card_frame_widget.winfo_rooty() - drop_area_height - drop_area_spacing

        main_window_geometry = [int(a) for a in re.split('[+x]', self.main_window.geometry())]
        main_window_end_pos_x = main_window_geometry[0] + main_window_geometry[2]
        drop_areas_frame_pos_x_offset = drop_areas_frame_pos_x + drop_areas_frame_width - main_window_end_pos_x
        if drop_areas_frame_pos_x_offset >= 0:
            drop_areas_frame_pos_x -= drop_areas_frame_pos_x_offset + drop_area_spacing

        # use a Toplevel window, overridedirect and "-topmost" attribute to trick tkinter into
        # displaying this window on top in a desired position
        self.drop_areas_frame = tk.Toplevel(self.main_window, padx=0, pady=0, background=self.COLORS['button'], borderwidth=drop_areas_frame_border)
        self.drop_areas_frame.geometry(f"{drop_areas_frame_width}x{drop_area_height + drop_area_spacing + drop_areas_title_text_pos_y}+{drop_areas_frame_pos_x}+{drop_areas_frame_pos_y}")
        self.drop_areas_frame.overrideredirect(True)
        self.drop_areas_frame.wm_attributes("-topmost", True)

        # canvas to paint drop areas onto
        canvas_width = (drop_area_width + drop_area_spacing) * (len(self.drop_areas)) + drop_area_spacing
        canvas = tk.Canvas(self.drop_areas_frame,
                           borderwidth=0,
                           bg="white",
                           width=canvas_width)
        canvas.pack()
        for drop_area in self.drop_areas:
            canvas.create_rectangle(drop_area['x1'], drop_area['y1'], drop_area['x2'], drop_area['y2'], fill=drop_area['color'])
            canvas.create_text(drop_area['x1'] + drop_area_width / 2, drop_area['y1'] + drop_area_height / 2, text=drop_area['name'], fill='black')
        canvas.create_text(canvas_width / 2, drop_areas_title_text_pos_y, text=drop_areas_title, fill='black')

    def on_drop(self, event):
        dragged_widget_name = event.widget.winfo_name()
        if dragged_widget_name not in self.dragged_widgets:
            return
        cursor_pos_x, cursor_pos_y = self.get_cursor_pos()
        self.dragged_widgets.remove(dragged_widget_name)
        event.widget.config(cursor="hand2")
        if self.drop_areas_frame is None:
            return
        drop_canvas = self.drop_areas_frame.winfo_children()[0]
        for i in range(len(self.drop_areas)):
            drop_top_left_x = self.drop_areas[i]['x1']
            drop_top_left_y = self.drop_areas[i]['y1']
            drop_bottom_right_x = self.drop_areas[i]['x2']
            drop_bottom_right_y = self.drop_areas[i]['y2']
            canvas_offset_x = drop_canvas.winfo_rootx()
            canvas_offset_y = drop_canvas.winfo_rooty()
            drop_top_left_x += canvas_offset_x
            drop_top_left_y += canvas_offset_y
            drop_bottom_right_x += canvas_offset_x
            drop_bottom_right_y += canvas_offset_y
            if drop_top_left_x < cursor_pos_x < drop_bottom_right_x and drop_top_left_y < cursor_pos_y < drop_bottom_right_y:
                self.drop_areas[i]['functor']()
                break
        self.drop_areas.clear()
        self.clear_drop_areas_frame()

    def draw_editor_panel(self):
        # EDITION FRAME
        edition_frame = tk.Frame(self.main_window, bg=self.COLORS['editor-background'], width=20)
        edition_frame.grid(row=0, column=0, sticky=tk.NSEW)
        self.main_window.grid_rowconfigure(0, weight=1)
        self.main_window.grid_columnconfigure(0, weight=1)
        
        # HEADER
        editor_header = tk.Frame(edition_frame, bg=self.COLORS['editor-background'])
        editor_header.pack(side='top', fill='both', expand=0, padx=10, pady=0)

        load_button = self.create_button(
            editor_header,
            text="📂",
            bordersize=2,
            color=self.COLORS['button'],
            activetextcolor=self.COLORS['main-background'],
            command=self.open_file,
            tooltip="Open file"
        )
        load_button.pack(side="right", padx=(10,0), pady=10, anchor=tk.NE)

        save_button = self.create_button(
            editor_header,
            text="⟳",
            bordersize=2,
            color=self.COLORS['button'],
            activetextcolor=self.COLORS['main-background'],
            command=self.reload_and_create_file,
            tooltip="Reload UI and save file"
        )
        save_button.pack(side="right", padx=(10,0), pady=10, anchor=tk.NE)

        # Light mode / dark mode switch
        button_color = self.COLORS['button']

        darkmode_button_border = tk.Frame(
            editor_header,
            bg=button_color
        )
        darkmode_button_border.pack(side="left", padx=(10,0), pady=10, anchor=tk.NE)
        darkmode_button = tk.Label(
            darkmode_button_border, 
            text='🔆', 
            relief='flat', 
            bg=self.COLORS['editor-background'], 
            fg=button_color,
            font=('arial', 12))
        darkmode_button.pack(side="left", padx=2, pady=2)
        darkmode_button.bind("<Button-1>", self.switch_darkmode)

        darkmode_button = tk.Label(
            darkmode_button_border, 
            text='🌙', 
            relief='flat', 
            bg=button_color, 
            fg=self.COLORS['editor-background'],
            font=('arial', 12))
        darkmode_button.pack(side="left", padx=2, pady=2)
        darkmode_button.bind("<Button-1>", self.switch_darkmode)
        # END Light mode / dark mode switch

        #END HEADER

        # Separator
        tk.Frame(edition_frame, height=1, bg=self.COLORS['main-text']).pack(side='top', fill='x')

        # MEMO
        cheat_sheet = tk.Label(edition_frame, text='------ Memo ------\n'
            'x \t\t—  done\n'
            f'{self.KANBAN_KEY}:{self.KANBAN_VAL_IN_PROGRESS} \t—  {self.COLUMN_NAME_IN_PROGRESS}\n'
            f'{self.KANBAN_KEY}:{self.KANBAN_VAL_VALIDATION} \t—  {self.COLUMN_NAME_VALIDATION}\n'
            'Ctrl + s \t\t—  refresh and save\n'
            'Alt + ↑ / ↓ \t—  move line up / down\n',
            bg=self.COLORS['editor-background'],
            anchor=tk.NW,
            justify='left',
            fg=self.COLORS['main-text'],
            font=tkFont.nametofont('main'),
        )
        cheat_sheet.pack(side="top", fill="x", padx=10)
        # MEMO END

        # Separator
        tk.Frame(
            edition_frame, height=1, bg=self.COLORS['main-text']).pack(side='top', fill='x')
        
        # EDITOR
        self.text_editor = tk.Text(
            edition_frame, 
            bg=self.COLORS['editor-background'], 
            insertbackground=self.COLORS['editor-text'], 
            fg=self.COLORS['editor-text'], 
            relief="flat", 
            width=40,
            height=10,
            maxundo=10,
            undo=True,
            wrap=tk.WORD,
            spacing1=10,
            spacing3=10,
            insertwidth=3,
        )
        self.text_editor.pack(side="top", fill="both", expand=1, padx=10, pady=10)
        self.text_editor.tag_configure('pair', background=self.COLORS['done-card-background'])
        self.text_editor.tag_configure('current_pos', background=self.COLORS['project'])
        self.text_editor.tag_configure('insert', background='red')

        # EDITOR TOOLBAR
        editor_toolbar = tk.Frame(edition_frame, bg=self.COLORS['editor-background'])
        editor_toolbar.pack(side='top', padx=10, pady=10, fill='both')

        # Move to todo
        self.create_button(
            editor_toolbar, 
            '✅→⚫', 
            self.COLORS[self.COLUMN_NAME_TODO], 
            command=self.move_to_todo,
            tooltip=f"Move task to {self.COLUMN_NAME_TODO}"
        ).grid(row=0, sticky='ew', column=0, padx=5, pady=5)

        # Cycle through priorities
        self.create_button(
            editor_toolbar,
            '⧉ ↻',
            self.COLORS['priority_color_scale'][4],
            command=self.change_priority,
            tooltip="Change priority to higher"
        ).grid(row=0, sticky='ew', column=4, padx=5, pady=5)

        # Move to In progress
        self.create_button(
            editor_toolbar,
            '✅→⚫',
            self.COLORS[self.COLUMN_NAME_IN_PROGRESS],
            command=self.move_to_in_progress,
            tooltip=f"Move task to {self.COLUMN_NAME_IN_PROGRESS}"
        ).grid(row=0, sticky='ew', column=1, padx=5, pady=5)

        # Move to Validation
        self.create_button(
            editor_toolbar,
            '✅→⚫',
            self.COLORS[self.COLUMN_NAME_VALIDATION],
            command=self.move_to_validation,
            tooltip=f"Move task to {self.COLUMN_NAME_VALIDATION}"
        ).grid(row=0, sticky='ew', column=2, padx=5, pady=5)

        # Move to Done
        self.create_button(
            editor_toolbar,
            '✅→⚫',
            self.COLORS[self.COLUMN_NAME_DONE],
            command=self.move_to_done,
            tooltip=f"Move task to {self.COLUMN_NAME_DONE}"
        ).grid(row=0, sticky='ew', column=3, padx=5, pady=5)

        # Set prios A..E
        self.create_button(
            editor_toolbar,
            f'⧉ A',
            self.COLORS['priority_color_scale'][0],
            command=self.change_priority_to_A,
            tooltip="Set priority to A"
        ).grid(row=3, sticky='ew', column=0, padx=5, pady=5)

        self.create_button(
            editor_toolbar,
            f'⧉ B',
            self.COLORS['priority_color_scale'][1],
            command=self.change_priority_to_B,
            tooltip="Set priority to B"
        ).grid(row=3, sticky='ew', column=1, padx=5, pady=5)

        self.create_button(
            editor_toolbar,
            f'⧉ C',
            self.COLORS['priority_color_scale'][2],
            command=self.change_priority_to_C,
            tooltip="Set priority to C"
        ).grid(row=3, sticky='ew', column=2, padx=5, pady=5)

        self.create_button(
            editor_toolbar,
            f'⧉ D',
            self.COLORS['priority_color_scale'][3],
            command=self.change_priority_to_D,
            tooltip="Set priority to D"
        ).grid(row=3, sticky='ew', column=3, padx=5, pady=5)

        self.create_button(
            editor_toolbar,
            f'⧉ E',
            self.COLORS['priority_color_scale'][4],
            command=self.change_priority_to_E,
            tooltip="Set priority to E"
        ).grid(row=3, sticky='ew', column=4, padx=5, pady=5)

        self.create_button(
            editor_toolbar,
            f'⧉ ☒',
            self.COLORS['important'],
            command=lambda: self.change_priority(None, ''),
            tooltip="Remove priority"
        ).grid(row=2, sticky='ew', column=4, padx=5, pady=5)
    
        # Add date
        self.create_button(
            editor_toolbar, 
            '+ date', 
            self.COLORS['button'], 
            command=self.add_date
        ).grid(row=2, sticky='ew', column=0, padx=5, pady=5)

        # Move line up
        self.create_button(
            editor_toolbar, 
            '↑', 
            self.COLORS['button'], 
            command=self.move_line_up,
            tooltip="Move line up"
        ).grid(row=2, sticky='ew', column=1, padx=5, pady=5)

        # Move line down
        self.create_button(
            editor_toolbar, 
            '↓', 
            self.COLORS['button'], 
            command=self.move_line_down,
            tooltip="Move line down"
        ).grid(row=2, sticky='ew', column=2, padx=5, pady=5)

        # Delete line
        self.create_button(
            editor_toolbar, 
            'Delete', 
            self.COLORS['button'], 
            command=self.remove_line,
            tooltip="Remove current line"
        ).grid(row=2, sticky='ew', column=3, padx=5, pady=5)

        editor_toolbar.columnconfigure(0, weight=1, uniform='toolbar-item')
        editor_toolbar.columnconfigure(1, weight=1, uniform='toolbar-item')
        editor_toolbar.columnconfigure(2, weight=1, uniform='toolbar-item')
        editor_toolbar.columnconfigure(3, weight=1, uniform='toolbar-item')
        editor_toolbar.columnconfigure(4, weight=1, uniform='toolbar-item')
        # EDITOR TOOLBAR END

        #EDITOR END

        # Bind all the option to update and save the file
        self.text_editor.bind('<Return>', self.return_pressed)
        self.text_editor.bind('<BackSpace>', self.return_pressed)
        self.text_editor.bind('<Control-space>', self.reload_and_save)
        self.text_editor.bind('<F5>', self.reload_and_save)

        # Bind navigation keys for proper tasks highlights
        # todo: make this more efficient, no need to update on every left/right, also no need to update editor colors
        self.text_editor.bind('<Up>', self.return_pressed)
        self.text_editor.bind('<Down>', self.return_pressed)
        self.text_editor.bind('<Right>', self.return_pressed)
        self.text_editor.bind('<Left>', self.return_pressed)
        self.text_editor.bind('<Control-End>', self.return_pressed)
        self.text_editor.bind('<Control-Home>', self.return_pressed)
        self.text_editor.bind('<Button-1>', self.return_pressed)

        # Shortkeys
        self.text_editor.bind('<Alt-Up>', self.move_line_up)
        self.text_editor.bind('<Alt-Down>', self.move_line_down)
        self.text_editor.bind('<Control-Key-1>', self.move_to_todo)
        self.text_editor.bind('<Control-Key-2>', self.change_priority)
        self.text_editor.bind('<Control-Key-3>', self.move_to_in_progress)
        self.text_editor.bind('<Control-Key-4>', self.move_to_validation)
        self.text_editor.bind('<Control-Key-5>', self.move_to_done)
    

    def draw_content_frame(self):
        # Create content view that will display kanban

        # SCROLLABLE CANVAS
        # Use canvas to make content view scrollable
        self.content_canvas = tk.Canvas(
            self.main_window, 
            bg=self.COLORS['main-background'], 
            bd=0, 
            highlightthickness=0, 
            relief=tk.FLAT
        )
        self.content_canvas.grid(row=0, column=1, sticky=tk.NSEW, padx=10, pady=10)
        
        # Give more space to the kanban view
        self.main_window.grid_columnconfigure(1, weight=6)

        # The frame inside the canvas. It manage the widget displayed inside the canvas
        self.content_frame = tk.Frame(self.content_canvas, bg=self.COLORS['main-background'])


        content_scrollbar = tk.Scrollbar(
            self.main_window, 
            orient="vertical", 
            command=self.content_canvas.yview
        )
        content_scrollbar.grid(row=0, column=2, sticky='ns')
        
        self.canvas_frame = self.content_canvas.create_window(
            (0, 0), window=self.content_frame, anchor="nw")

        # Attach the scroll bar position to the visible region of the canvas
        self.content_canvas.configure(yscrollcommand=content_scrollbar.set)
        # END SCROLLABLE CANVAS

        # Prepare progress bars and kanban itself
        self.progress_bar = tk.Frame(self.content_frame, height=15, bg=self.COLORS['done-card-background'])
        self.progress_bar.pack(side='top', fill='x', padx=10, pady=10)
        self.progress_bars = {}

        # position of the current sub progress bar
        sub_bar_pos = 0
        # number of the current column in the tkinter grid
        column_number = 0

        # Frame containing the kanban
        self.kanban_frame = tk.Frame(self.content_frame, bg=self.COLORS['main-background'])
        self.kanban_frame.pack(fill='both')

        # Create each column and its associated progress bar
        for key, column in self.ui_columns.items():
            column_color = self.COLORS[key + '-column']

            # Create the kanban column
            ui_column = tk.Frame(self.kanban_frame, bg=column_color)
            ui_column.grid(
                row=1, column=column_number, padx=10, pady=0, sticky='nwe')
            self.kanban_frame.grid_columnconfigure(
                column_number, weight=1, uniform="kanban")
            
            top_border = tk.Frame(
                ui_column, 
                bg=self.COLORS[key], 
                height=8
            )
            top_border.pack(fill='x', side="top", anchor=tk.W)

            title_color = self.COLORS[key]
            if title_color == self.COLORS[key + '-column']:
                title_color = self.COLORS['main-background']
            label = tk.Label(
                ui_column, 
                text=key, 
                fg=title_color, 
                bg=ui_column['bg'], 
                anchor=tk.W, 
                font=tkFont.nametofont('h2')
            )
            label.pack(padx=10, pady=(3, 10), fill='x', side="top", anchor=tk.W)

            ui_column_content = tk.Frame(ui_column, bg=ui_column['bg'], height=0)
            ui_column_content.pack(side='top', padx=10, pady=(0,10), fill='x')

            self.ui_columns[key] = ui_column
            self.ui_columns[key].content = ui_column_content

            
            # Create the progress bar associated to the column
            self.progress_bars[key] = {}
            self.progress_bars[key]['bar'] = tk.Frame(
                self.progress_bar, bg=self.COLORS[key])
            self.progress_bars[key]['bar'].place(
                relx=sub_bar_pos, relwidth=0.25, relheight=1)
            
            # Add a label in the progress bar that display the number of tasks
            # in the column
            bar_label_text = key + ': -'
            self.progress_bars[key]['label'] = tk.Label(
                self.progress_bars[key]['bar'], 
                text=bar_label_text, 
                fg=self.COLORS['main-background'], 
                bg=self.progress_bars[key]['bar']['bg'], 
                font=('Arial', 8))
            self.progress_bars[key]['label'].pack(side='left', padx=5)
            
            sub_bar_pos += 0.25
            column_number += 1

        # Bind signals
        #self.content_canvas.bind('<Configure>', self.adapt_canvas_to_window)

        # Allow to bind the mousewheel event to the canvas and scroll through it
        # with the wheel
        self.content_canvas.bind('<Enter>', self.bind_to_mousewheel)
        self.content_canvas.bind('<Leave>', self.unbind_to_mousewheel)

        # Move the scroll region according to the scroll
        self.content_frame.bind(
            "<Configure>",
            lambda e: self.content_canvas.configure(
                scrollregion=self.content_canvas.bbox("all")
            )
        )

        # resize kanban frame when window is resied
        self.content_canvas.bind('<Configure>', self.on_window_resize)
    

    def create_button(
        self,
        parent, 
        text="button",
        color="black",
        activetextcolor="white",
        bordersize=2,
        command=None,
        tooltip=None,
    ):
        """Create a button with a border and no background"""
        button_frame = tk.Frame(
            parent,
            bg=color
        )
        button = tk.Button(
            button_frame,
            text=text,
            relief='flat',
            bg=parent['bg'],
            fg=color,
            activebackground=color,
            activeforeground=activetextcolor,
            borderwidth=0,
            font=('main', 12),
            command=command)
        button.pack(padx=bordersize, pady=bordersize, fill='both')
        if tooltip is not None:
            hovertip = Hovertip(button, tooltip)
        return button_frame


    def fread(self, filename):
        """Read file and close the file."""
        with open(filename, 'r', encoding='utf8') as f:
            return f.read()

    def fwrite(self, filename, text):
        """Write content to file and close the file."""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(text)

    def parse_todo_txt(self, p_todo_txt):
        """Parse a todo txt content and return data as a dictionary"""
        tasks = {}
        for col in self.COLUMNS_NAMES:
            tasks[col] = []

        # Erase the columns content
        for ui_column_name, ui_column in self.ui_columns.items():
            ui_column.content.pack_forget()
            for widget in ui_column.content.winfo_children():
                widget.destroy()

        todo_list = p_todo_txt.split("\n")

        cards_data = []
        for index, task in enumerate(todo_list):
            if len(task) != 0:
                task_data = re.match(
                    r'^(?P<isDone>x )? '
                    r'?(?P<priority>\([A-Z]\))? '
                    r'?(?P<dates>\d\d\d\d-\d\d-\d\d( \d\d\d\d-\d\d-\d\d)?)? '
                    r'?(?P<subject>.+)',
                    task)

                # special key-vals, context or project tags may occur basically everywhere in the line,
                # so don't try to fit it into the structured regex above, just make a new search
                special_kv_r = re.compile(r'(?P<key>[^:\s]+):(?P<val>[^:\s]+)')
                special_kv_data = [m.groupdict() for m in special_kv_r.finditer(task)]

                project_r = re.compile(r' (?P<project>\+\S+)')
                project_data = [m.groupdict() for m in project_r.finditer(task)]

                context_r = re.compile(r' (?P<context>@\S+)')
                context_data = [m.groupdict() for m in context_r.finditer(task)]

                task = task_data.groupdict()
                task['is_important'] = False

                subject = task.get('subject', '???')

                # remove any special key-val strings, project and context tags from the subject text for clarity
                subject = re.sub(special_kv_r, "", subject)
                subject = re.sub(project_r, "", subject)
                subject = re.sub(context_r, "", subject)

                category = self.COLUMN_NAME_TODO

                category_map = {
                    self.KANBAN_VAL_IN_PROGRESS: self.COLUMN_NAME_IN_PROGRESS,
                    self.KANBAN_VAL_VALIDATION: self.COLUMN_NAME_VALIDATION,
                }

                for i in range(0, len(special_kv_data)):
                    kv = special_kv_data[i]
                    if kv['key'] == self.KANBAN_KEY:
                        v = kv['val']
                        if v in category_map.keys():
                            category = category_map[v]
                            break

                if task.get("isDone"):
                    category = self.COLUMN_NAME_DONE

                priority = None
                if task.get("priority"):
                    priority = task['priority'][1]  # get only letter without parenthesis

                tasks[category].append(task)

                start_date = None
                end_date = None
                if task.get('dates'):
                    dates = []
                    dates = task.get('dates').split(' ')
                    if len(dates) == 1:
                        start_date = date.fromisoformat(dates[0])
                    elif len(dates) == 2:
                        start_date = date.fromisoformat(dates[1])
                        end_date = date.fromisoformat(dates[0])

                card_bg = self.COLORS['card-background']
                font = 'main'
                if category == self.COLUMN_NAME_DONE:
                    card_bg = self.COLORS['done-card-background']
                    font = 'done-task'

                card_parent = self.ui_columns[category].content

                cards_data.append({
                    'parent': card_parent,
                    'subject': subject,
                    'bg': card_bg,
                    'font': font,
                    'project': project_data,
                    'context': context_data,
                    'start_date': start_date,
                    'end_date': end_date,
                    'state': category,
                    'name': "task#" + str(index + 1),
                    'special_kv_data': special_kv_data,
                    'priority': priority
                })

        cards_data.sort(key=lambda d: d['priority'] if d['priority'] is not None else 'z')
        for card in cards_data:
            self.draw_card(
                card['parent'],
                card['subject'],
                card['bg'],
                card['font'],
                project=card['project'],
                context=card['context'],
                start_date=card['start_date'],
                end_date=card['end_date'],
                state=card['state'],
                name=card['name'],
                special_kv_data=card['special_kv_data'],
                priority=card['priority']
            )

        # Compute proportion for each column tasks and update progress bars
        tasks_number = {}
        for col in self.COLUMNS_NAMES:
            tasks_number[col] = len(tasks[col])

        total_tasks = 0

        for key, number in tasks_number.items():
            total_tasks += number

        if total_tasks > 0:
            percentages = {}
            for col in self.COLUMNS_NAMES:
                percentages[col] = tasks_number[col] / total_tasks

            bar_x = 0

            for key, progress_bar in self.progress_bars.items():
                progress_bar['bar'].place(relx=bar_x, relwidth=percentages[key], relheight=1)
                label_text = f"{tasks_number[key]}"
                progress_bar['label'].config(text=label_text)
                bar_x += percentages[key]

        for ui_column_name, ui_column in self.ui_columns.items():
            tmp_frame = tk.Frame(ui_column.content, width=0, height=0)
            tmp_frame.pack()
            ui_column.content.update()
            tmp_frame.destroy()
            ui_column.content.pack(side='top', padx=10, pady=(0,10), fill='x')
        
        self.update_editor_line_colors()

        self.main_window.update()

        return tasks;


    def draw_card(
        self, 
        parent, 
        subject, 
        bg, 
        font='main', 
        project=None, 
        context=None, 
        start_date=None,
        end_date=None,
        state=COLUMN_NAME_TODO,
        name="",
        special_kv_data=None,
        priority=None
    ):
        def bind_highlight_and_drag_n_drop(widget):
            widget.bind('<Button-1>', self.on_click)
            widget.bind('<B1-Motion>', self.on_drag_init)
            widget.bind('<ButtonRelease>', self.on_drop)

        def get_widget_name(subject_name):
            ret_name = str(get_widget_name.counter) + subject_name
            get_widget_name.counter += 1
            return ret_name
        get_widget_name.counter = 0

        # Create the card frame
        ui_card_highlight = tk.Frame(parent, bd=2, bg=self.COLORS[f'{self.COLUMN_NAME_DONE}-column'], height=200, name="highlightFrame"+name)
        ui_card = tk.Frame(ui_card_highlight, bd=0, bg=bg, height=200, cursor='hand2', name=get_widget_name(name))

        subject_padx = 10

        # If needed, add a color border for priority marking
        if priority is not None:
            prio_color = self.get_priority_color(priority)
            important_border = tk.Frame(ui_card, bg=prio_color, width="3", name=get_widget_name(name))
            bind_highlight_and_drag_n_drop(important_border)
            important_border.pack(side="left", fill='y')
            important_label = tk.Label(
                ui_card,
                text=priority,
                fg=prio_color,
                bg=ui_card['bg'],
                anchor=tk.W,
                font=tkFont.Font(family='arial', size=18, weight=tkFont.BOLD),
                name=get_widget_name(name)
            )
            important_label.pack(side="left", anchor=tk.NW, padx=0, pady=(5,0))
            bind_highlight_and_drag_n_drop(important_label)
            subject_padx = 0

        card_label = tk.Label(
            ui_card, 
            text=subject, 
            fg=self.COLORS['main-text'], 
            bg=ui_card['bg'], 
            anchor=tk.W, 
            wraplength=200, 
            justify='left',
            font=tkFont.nametofont(font),
            name=get_widget_name(name)
        )

        # Adapt elide length when width change
        card_label.bind("<Configure>", self.on_card_width_changed)
        bind_highlight_and_drag_n_drop(card_label)
        card_label.pack(padx=subject_padx, pady=5, fill='x', side="top", anchor=tk.W)

        # If needed, show the task duration
        if start_date:
            duration = 0
            if not end_date:
                end_date = self.current_date

            duration = end_date.toordinal() - start_date.toordinal()
            duration_string = "%d days" % (duration)

            duration_label = tk.Label(
                ui_card, 
                text = duration_string,
                fg=self.COLORS[state], 
                bg=ui_card['bg'], 
                anchor=tk.W, 
                justify='left',
                font=("Arial", 8),
                wraplength=85,
                name=get_widget_name(name)
            )
            if (project or context) and (len(project) > 0 or len(context) > 0):
                duration_label.pack(side="top", anchor=tk.NW, padx=10, pady=0)
            else:
                duration_label.pack(side="top", anchor=tk.NW, padx=10, pady=(0,10))
            bind_highlight_and_drag_n_drop(duration_label)

        # Add project and context tags if needed
        if project and len(project) > 0:
            project_string = ", ".join([p["project"] for p in project])
            project_label = tk.Label(
                ui_card, 
                text=project_string, 
                fg=self.COLORS["project"], 
                bg=ui_card['bg'], 
                anchor=tk.E,
                name=get_widget_name(name)
            )
            project_label.pack(padx=10, pady=5, fill='x', side="top", anchor=tk.E)
            bind_highlight_and_drag_n_drop(project_label)

        if context and len(context) > 0:
            context_string = ", ".join([c["context"] for c in context])
            context_label = tk.Label(
                ui_card, 
                text=context_string, 
                fg=self.COLORS['context'], 
                bg=ui_card['bg'], 
                anchor=tk.E,
                name=get_widget_name(name)
            )
            context_label.pack(padx=10, pady=5, fill='x', side="top", anchor=tk.E)
            bind_highlight_and_drag_n_drop(context_label)

        if special_kv_data is not None and len(special_kv_data) > 0:
            special_kv_data_string = ", ".join([f"{special_kv_data_entry['key']}:{special_kv_data_entry['val']}" for
                                                special_kv_data_entry in special_kv_data])
            special_kv_entry_label = tk.Label(
                ui_card,
                text=special_kv_data_string,
                fg=self.COLORS['kv-data'],
                bg=ui_card['bg'],
                anchor=tk.E,
                name=get_widget_name(name)
            )
            special_kv_entry_label.pack(padx=10, pady=5, fill='x', side="top", anchor=tk.E)
            bind_highlight_and_drag_n_drop(special_kv_entry_label)

        ui_card.pack(padx=1, pady=(0, 10), side="top", fill='x', expand=1, anchor=tk.NW)
        ui_card_highlight.pack(padx=0, pady=(0, 1), side="top", fill='x', expand=1, anchor=tk.NW)
        bind_highlight_and_drag_n_drop(ui_card)

        return ui_card


    def open_file(self, event=None):
        """Open a dialog to select a file to load"""
        self.file = filedialog.askopenfilename(
            initialdir='.', 
            filetypes=[("todo list file", "*todo.txt"), ("txt file", "*.txt")],
            title='Choose a todo list to display')
        
        self.load_file()


    def load_file(self):
        if os.path.isfile(self.file):
            todo_txt = self.fread(self.file)
            self.text_editor.delete('1.0', 'end')
            self.text_editor.insert(tk.INSERT, todo_txt)
            self.text_editor.focus()
            self.text_editor.mark_set('insert', 'end')
            self.text_editor.see('insert')
            todo_cards = self.parse_todo_txt(todo_txt)
            self.main_window.title(f"KanbanTxt - {pathlib.Path(self.file).name}")
            # self.update_ui(todo_cards)


    def reload_and_save(self, event=None):
        """Reload the kanban and save the editor content in the current todo.txt
            file """
        data = self.parse_todo_txt(self.text_editor.get("1.0", "end-1c"))
        # self.update_ui(data)
        if self.file:
            self.fwrite(self.file, self.text_editor.get("1.0", "end-1c"))


    def reload_and_create_file(self, event=None):
        """In case no file were open, open a dialog to choose where to save the 
            current data"""
        if not os.path.isfile(self.file):
            new_file = filedialog.asksaveasfile(
                initialdir='.',
                defaultextension='.todo.txt',
                title='Choose a location to save your todo list',
                confirmoverwrite=True,
                filetypes=[('todo list file', '*todo.txt')])
            
            if not new_file:
                return

            # just create the file
            self.file = new_file.name
            new_file.close()
            
            # as tk does'nt support double extensions, we have to write it here
            file_path, extension = os.path.splitext(self.file)
            if extension != 'todo.txt':
                os.rename(self.file, file_path + '.todo.txt')
                self.file = file_path + '.todo.txt'
        
        self.reload_and_save()


    # BINDING CALLBACKS

    def adapt_canvas_to_window(self, event):
        """Resize canvas when window is resized"""
        canvas_width = event.width
        self.content_canvas.itemconfig(self.canvas_frame, width = canvas_width)
                
    def hide_content(self):
        self.progress_bar.pack_forget()
        self.kanban_frame.pack_forget()


    def display_content(self):
        self.progress_bar.pack(side='top', fill='x', padx=10, pady=10)
        self.kanban_frame.pack(fill='both')


    def on_card_width_changed(self, event):
        """Adapt todo cards text wrapping when the window is resized"""
        event.widget['wraplength'] = event.width - 20
    

    def bind_to_mousewheel(self, event):
        """Allow scroll event while pointing the kanban frame"""
        # with Windows OS
        event.widget.bind_all("<MouseWheel>", self.scroll)
        # with Linux OS
        event.widget.bind_all("<Button-4>", self.scroll)
        event.widget.bind_all("<Button-5>", self.scroll)
    

    def unbind_to_mousewheel(self, event):
        """Disable scroll event while not pointing the kanban frame"""
        # with Windows OS
        event.widget.unbind_all("<MouseWheel>")
        # with Linux OS
        event.widget.unbind_all("<Button-4>")
        event.widget.unbind_all("<Button-5>")


    def scroll(self, event):
        """Scroll through the kanban frame"""
        self.content_canvas.yview_scroll(int(-1*(event.delta/120)), "units")


    def switch_darkmode(self, event):
        """Switch from light and dark mode, destroy the UI and recreate it to
            apply the modification"""
        self.darkmode = not self.darkmode

        window_geometry = self.main_window.geometry()
        window_state = self.main_window.state()
        width, height, x, y = re.split("[x+]", window_geometry)

        self.main_window.destroy()
        self.draw_ui(int(width), int(height), int(x), int(y))
        self.main_window.state(window_state)


    def move_line_up(self, event=None):
        current_line = self.text_editor.get("insert linestart", "insert lineend")
        self.text_editor.delete("insert linestart", "insert lineend + 1c")
        self.text_editor.insert("insert linestart -1l", current_line + '\n')
        if event:
            self.text_editor.mark_set('insert', 'insert linestart -1l')
        else:
            self.text_editor.mark_set('insert', 'insert linestart -2l')
        
        self.update_editor_line_colors()
        #self.reload_and_save()
    

    def move_line_down(self, event=None):
        current_line = self.text_editor.get("insert linestart", "insert lineend")
        self.text_editor.delete("insert linestart", "insert lineend + 1c")
        self.text_editor.insert("insert linestart +1l", current_line + '\n')
        if event:
            self.text_editor.mark_set('insert', 'insert lineend')
        else:
            self.text_editor.mark_set('insert', 'insert lineend +1l')
        
        self.update_editor_line_colors()
        # self.reload_and_save()
    

    def remove_line(self, event=None):
        self.text_editor.delete("insert linestart", "insert lineend + 1c")


    def set_state(self, task, newState):
        task = re.sub(rf'\s{self.KANBAN_KEY}:[^\s^:]+', '', task)
        task = re.sub(r'^x ', '', task)
        task = re.sub(r'^ ', '', task)
        if newState == 'x':
            task = newState + ' ' + task
        else:
            task = task + newState
        return task

    def set_priority(self, task, new_priority):
        priority_done_r = re.compile(r'^x \([A-Z]\) ')
        priority_not_done_r = re.compile(r'^\([A-Z]\) ')
        had_priority = True if re.match(priority_done_r, task) or re.match(priority_not_done_r, task) else False
        is_done = True if re.match(r'^x ', task) else False

        if is_done:
            if had_priority:
                result = f"x {re.sub(priority_done_r, new_priority, task)}"
            else:
                task_without_done_marking = task[2:]
                result = f"x {new_priority}{task_without_done_marking}"
        else:
            if had_priority:
                result = re.sub(priority_not_done_r, new_priority, task)
            else:
                result = f"{new_priority}{task}"
        return result

    def set_editor_line_state(self, new_state):
        current_line = self.text_editor.get("insert linestart", "insert lineend")
        current_line = self.set_state(current_line, new_state)
        self.text_editor.delete("insert linestart", "insert lineend + 1c")
        self.text_editor.insert("insert linestart", current_line + '\n')
        self.text_editor.mark_set('insert', 'insert linestart -1l')
        self.reload_and_save()

    def set_editor_line_priority(self, new_priority_override=None):
        current_line = self.text_editor.get("insert linestart", "insert lineend")
        if new_priority_override is None:
            priority_match = re.match(r'^(?P<isDone>x )?(?P<priority>\([A-Z]\))?', current_line)
            highest_prio = 'A'
            lowest_prio = 'E'
            new_priority = f"({lowest_prio}) "
            if priority_match['priority']:
                current_priority = priority_match['priority']
                current_priority_code = ord(current_priority[1])
                new_priority_code = current_priority_code - 1
                if current_priority_code == ord(highest_prio):
                    new_priority = ""
                else:
                    if new_priority_code < ord(highest_prio):
                        new_priority_code = ord(lowest_prio)
                    new_priority = f"({chr(new_priority_code)}) "
        else:
            if len(new_priority_override) > 0:
                new_priority = f"({new_priority_override}) "
            else:
                new_priority = f""

        current_line = self.set_priority(current_line, new_priority)
        self.text_editor.delete("insert linestart", "insert lineend + 1c")
        self.text_editor.insert("insert linestart", current_line + '\n')
        self.text_editor.mark_set('insert', 'insert linestart -1l')
        self.reload_and_save()

    def move_to_todo(self, event=None):
        self.set_editor_line_state('')

    def change_priority_to_A(self):
        self.change_priority(None, "A")

    def change_priority_to_B(self):
        self.change_priority(None, "B")

    def change_priority_to_C(self):
        self.change_priority(None, "C")
    def change_priority_to_D(self):
        self.change_priority(None, "D")

    def change_priority_to_E(self):
        self.change_priority(None, "E")

    def change_priority(self, event=None, new_priority=None):
        self.set_editor_line_priority(new_priority)

    def move_to_in_progress(self, event=None):
        self.set_editor_line_state(f' {self.KANBAN_KEY}:{self.KANBAN_VAL_IN_PROGRESS}')

    def move_to_validation(self, event=None):
        self.set_editor_line_state(f' {self.KANBAN_KEY}:{self.KANBAN_VAL_VALIDATION}')

    def move_to_done(self, event=None):
        self.set_editor_line_state('x')

    def add_date(self, event=None):
        current_line = self.text_editor.get("insert linestart", "insert lineend")
        match = re.match(r'x|\([A-C]\) ', current_line)
        insert_index = 0
        if match:
            insert_index = match.end()
        
        self.text_editor.insert("insert linestart +%dc" % (insert_index), str(self.current_date) + " ")
    

    def on_window_resize(self, event):
        self.hide_content()
        
        if self._after_id:
            self.main_window.after_cancel(self._after_id)
        
        self._after_id = self.main_window.after(100, self.update_canvas, event)


    def update_canvas(self, event):
        self.content_canvas.itemconfig(self.canvas_frame, width = event.width)

        if event.width < 700:
            index = 1
            for column_name, column in self.ui_columns.items():
                column.grid(
                    row=index, column=0, pady=10, sticky='nwe', columnspan=4)
                index += 1
            
        else:
            index = 0
            for column_name, column in self.ui_columns.items():
                column.grid(
                    row=1, column=index, padx=10, sticky='nwe', columnspan=1)
                index += 1

        self.display_content()
        pass

    def return_pressed(self, event=None):
        self.main_window.after(100, self.update_editor_line_colors)

    def update_editor_line_colors(self, event=None):
        nb_line = int(self.text_editor.index('end-1c').split('.')[0])

        selected_line = int(self.text_editor.index(tk.INSERT).split('.')[0])
        task_card_found = False
        columns = self.kanban_frame.winfo_children()
        for column in columns:
            if task_card_found:
                break
            task_cards = column.winfo_children()[2].winfo_children()
            for task_card in task_cards:
                if task_card.winfo_name().endswith(f"task#{selected_line}"):
                    self.highlight_selected_task_card(task_card)
                    task_card_found = True
                    break
        if not task_card_found:
            self.highlight_selected_task_card(None)

        for line_idx in range(nb_line):
            self.text_editor.tag_remove('pair', str(line_idx) + '.0', str(line_idx) + '.0 lineend +1c')
            self.text_editor.tag_remove('current_pos', str(line_idx) + '.0', str(line_idx) + '.0 lineend +1c')
            if line_idx == selected_line:
                self.text_editor.tag_add('current_pos', str(line_idx) + '.0', str(line_idx) + '.0 lineend +1c')
            elif line_idx % 2 == 0:
                self.text_editor.tag_add('pair', str(line_idx) + '.0', str(line_idx) + '.0 lineend +1c')

    def get_task_card_frame_widget(self, any_subwidget):
        # get first parent which starts with "highlightFrame" in its name
        selected_task_card_frame = None
        parent = any_subwidget
        max_depth = 5
        for i in range(0, max_depth):
            if parent is None:
                break
            if parent.winfo_name().startswith("highlightFrame"):
                selected_task_card_frame = parent
                break
            parent = parent.master
        return selected_task_card_frame

    def highlight_selected_task_card(self, selected_widget):
        # get first parent which starts with "highlightFrame" in its name
        selected_highlight_frame = self.get_task_card_frame_widget(selected_widget)

        if self.selected_task_card is not None:
            try:
                self.selected_task_card.configure(background=self.COLORS[f'{self.COLUMN_NAME_DONE}-column'])
            except:
                self.selected_task_card = None

        if selected_highlight_frame is not None:
            selected_highlight_frame.configure(background=self.COLORS['project'])
            self.selected_task_card = selected_highlight_frame

    def highlight_task(self, event):
        self.clear_drop_areas_frame()
        selected_widget = event.widget
        self.highlight_selected_task_card(selected_widget)
        searched_task_line = selected_widget.winfo_name()[1:].replace("task#", "")
        self.text_editor.mark_set('insert', searched_task_line + ".0")
        self.text_editor.see('insert')
        self.return_pressed()

    def get_priority_color(self, current_priority):
        index = ord(current_priority) - ord('A')
        if index >= len(self.COLORS['priority_color_scale']) or index < 0:
            index = -1
        return self.COLORS['priority_color_scale'][index]


def main(args):
    app = KanbanTxtViewer(args.file, args.darkmode)
    if os.name == 'nt':
        app.main_window.state('zoomed')
    app.main_window.mainloop()
    

if __name__ == '__main__':
    if os.name == 'nt':
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('KanbanTxt')
    arg_parser = argparse.ArgumentParser(description='Display a todo.txt file as a kanban and allow to edit it')
    arg_parser.add_argument('--file', help='Path to a todo.txt file', required=False, default='', type=str)
    arg_parser.add_argument('--darkmode', help='Is the UI should use dark theme', required=False, action='store_true')
    args = arg_parser.parse_args()
    main(args)
