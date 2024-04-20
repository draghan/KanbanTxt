# KanbanTxt

A light todo.txt editor that display the to do list as a kanban board. See [here](https://github.com/todotxt/todo.txt) for a detailed description of the todo.txt format.

The goal was to have a one file script that open a tkinter GUI to edit my todo.txt files and displaying a kanban view of my tasks.

The interface looks as follows, with full support of the todo.txt format:

![Screenshot of the KanbanTxt window](./screenshot.png)

## Prerequisites

- Python 3
- Know the todo.txt format (see [here](https://github.com/todotxt/todo.txt) for a detailed description of the todo.txt format)

## Installation

Just download the KanbanTxt.py script.

## Usage

### Run KanbanTxt

```
python KanbanTxt.py
```

By adding the `--file` parameter it is possible to open a todo.txt file while opening KanbanTxt

```
python KanbanTxt.py --file=path/to/my/todo.txt
```

Or the button "Open" in the GUI allows to open a file through GUI.

### Edit the to do list

To edit the to do list you can use the integrated text editor to the left of the kanban board panel. To refresh the kanban view, press *ctrl + space*.

### Select a task

You can click on the text in a task card to move the cursor of text editor to the right line.

### Move a card to another column

I used the todo.txt special key-val tags to define in which column each task should appear.

- `knbn:in_progress` tag: A task is being work on, it's displayed in the "In progress" column. 
- `knbn:validate` tag: This task is done but need to be validate before considering it as finished. It goes to the *Validation* column.
- `x ` prefix: This task is finished and goes to the *Done* column.
- A task without a `knbn` key tag and without the `x ` prefix, goes to the *To Do* column, waiting to be treated.

You can also use *ctrl + 1-5* to move the task under the text editor cursor to the corresponding column.
1. To Do
2. Change priority
3. In progress
4. Validation
5. Done

Or you can do the same by using the buttons under the editor.

### Assign priority

To assign priority, use the last row of buttons under the editor.

Tasks are sorted in columns by their priority. 

Tasks with priority (A) are the most critical and displayed first, then goes (B), (C) and so on, up to (Z). Tasks without priority set are considered the lowest priority, even lower than (Z).

Tasks' priority is displayed next to their contents, with hot-map color coding for priorities A-E.

### Reorder the tasks in the text editor

The buttons with an up and a bottom arrow allow to move the current line of editor one step up or down. The same action can be done with the shortcut *alt + ↑* and *alt + ↓*. Note, that tasks are sorted by priority first, and then by the line number.

### Show the time spent on a task

Using the "+ date" button add the date of the day at the begining of a line in the editor. This allows to define a creation date and a completion date to the task.

If a creation date is provided, KanbanTxt will display the number of days elapsed from the creation date to the current day on the task. If a completion date is provided, KanbanTxt will add a label to show the time spent on the task.

### Use the dark theme

A little switch with a sun and a moon on the top left corner of the application allows to switch between light and dark mode. This setting is not saved and the program always start with the light theme. But you can launch KanbanTxt in dark mode by running: 

```
python KanbanTxt.py --darkmode
```

### Current support of the todo.txt format

- [x] priority prefixes
- [x] multiple project tags `+project`
- [x] multiple context tags `@context`
- [x] creation date
- [x] completion date
- [x] special key/value tags

