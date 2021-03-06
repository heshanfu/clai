#
# Copyright (C) 2020 IBM. All Rights Reserved.
#
# See LICENSE.txt file in the root directory
# of this source tree for licensing information.
#

import os
import tkinter as tk
from tkinter import ttk, messagebox
from typing import List

from clai.emulator.toggled_frame import ToggledFrame
from clai.emulator.emulator_presenter import EmulatorPresenter
from clai.server.command_message import Action


# pylint: disable=too-many-instance-attributes,protected-access,attribute-defined-outside-init,too-many-public-methods
class ClaiEmulator:

    def __init__(self):
        self.presenter = EmulatorPresenter(self.on_skills_ready, self.on_server_running, self.on_server_stopped)

    def launch(self):
        root = tk.Tk()
        root.geometry("900x600")
        self.add_toolbar(root)
        self.add_send_command_box(root)
        self.add_list_commands(root)

        root.protocol("WM_DELETE_WINDOW", lambda root=root: self.on_closing(root))
        root.createcommand('exit', lambda root=root: self.on_closing(root))

        root.mainloop()

    def on_closing(self, root):
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.presenter.stop_server()
            root.destroy()

    def on_skills_ready(self, skills_as_array: List[str]):
        self.selected_skills_dropmenu.configure(state="active")
        self.selected_skills_dropmenu["menu"].delete(0, 'end')

        for skill in skills_as_array[1:-1]:
            name_skill, active = self.clear_text(skill)
            self.selected_skills_dropmenu["menu"].add_command(
                label=name_skill,
                command=tk._setit(self.selected_skills, name_skill))

            if active:
                self.presenter.current_active_skill = self.extract_skill_name(name_skill)[0]
                self.selected_skills.set(name_skill)

    def on_server_running(self):
        self.run_button.configure(image=self.stop_image)

    def on_server_stopped(self):
        self.run_button.configure(image=self.run_image)

    # pylint: disable=unused-argument
    def on_skill_selected(self, *args):
        print(f"new skills {self.selected_skills.get()}")
        skill_name, installed = self.extract_skill_name(self.selected_skills.get())
        self.presenter.select_skill(skill_name, installed)

    def add_row(self, response: Action, response_post: Action):
        command_executed = response.suggested_command
        if not command_executed:
            command_executed = f"{response.origin_command} (executed origin)"
        toggled_frame = ToggledFrame(self.frame, text=command_executed, relief=tk.RAISED, borderwidth=1)
        toggled_frame.pack(fill="x", expand=1, pady=2, padx=2, anchor="n")

        first_row = ttk.Frame(toggled_frame.sub_frame)
        first_row.pack(fill="x", expand=True)
        ttk.Label(first_row, text=f"Original: {response.origin_command}").pack(side=tk.LEFT, padx=10)
        ttk.Label(first_row, text=f"Id: {self.presenter.command_id - 1}").pack(side=tk.RIGHT, padx=10)

        second_row = ttk.Frame(toggled_frame.sub_frame)
        second_row.pack(fill="x", expand=True)
        ttk.Label(second_row, text=f'Description: {self.remove_emoji(response.description)}') \
            .pack(side=tk.LEFT, padx=10)
        ttk.Label(second_row, text=f"Confidence:{response.confidence} Force: {response.execute}") \
            .pack(side=tk.RIGHT, padx=10)

        ttk.Label(toggled_frame.sub_frame, text=f'Post execution:').pack(side=tk.LEFT, padx=10)

        third_row = ttk.Frame(toggled_frame.sub_frame)
        third_row.pack(fill="x", expand=True)
        ttk.Label(third_row, text=f'Description: {self.remove_emoji(response_post.description)}') \
            .pack(side=tk.LEFT, padx=10)
        ttk.Label(third_row, text=f"Confidence:{response_post.confidence}") \
            .pack(side=tk.RIGHT, padx=10)

    def add_send_command_box(self, root):
        button_bar_frame = tk.Frame(root, bd=1, relief=tk.RAISED)
        send_button = tk.Button(button_bar_frame, padx=10, text='Send', command=self.on_send_click)
        send_button.pack(side=tk.RIGHT, padx=5)
        self.text_input = tk.StringVar()
        send_edit_text = tk.Entry(button_bar_frame, textvariable=self.text_input)
        send_edit_text.bind('<Return>', self.on_enter)
        send_edit_text.pack(side=tk.LEFT, fill=tk.X, expand=True)
        button_bar_frame.pack(side=tk.BOTTOM, pady=2, fill=tk.X)

    def add_toolbar(self, root):
        toolbar = tk.Frame(root, bd=1, relief=tk.RAISED)
        self.add_button(toolbar)
        self.add_skills_selector(root, toolbar)
        toolbar.pack(side=tk.TOP, fill=tk.X)

    def add_skills_selector(self, root, toolbar):
        label = ttk.Label(toolbar, text="Skills")
        label.pack(side=tk.LEFT, padx=2)

        self.selected_skills = tk.StringVar(root)
        self.selected_skills.set("")
        self.selected_skills.trace("w", self.on_skill_selected)
        self.selected_skills_dropmenu = tk.OptionMenu(toolbar, self.selected_skills, [])
        self.selected_skills_dropmenu.configure(state="disabled")
        self.selected_skills_dropmenu.pack(side=tk.LEFT, padx=2)

    def add_button(self, toolbar):
        path = os.path.dirname(os.path.abspath(__file__))
        self.run_image = tk.PhotoImage(file=f"{path}/run.gif")
        self.stop_image = tk.PhotoImage(file=f"{path}/stop.gif")
        self.run_button = ttk.Button(toolbar, image=self.run_image, command=self.on_run_click)
        self.run_button.pack(side=tk.LEFT, padx=2, pady=2)

    # pylint: disable=unused-argument
    def on_enter(self, event):
        self.send_command(self.text_input.get())

    def on_send_click(self):
        self.send_command(self.text_input.get())

    def send_command(self, command):
        response, response_post = self.presenter.send_message(command)
        self.add_row(response, response_post)
        self.text_input.set("")

    def on_run_click(self):
        if not self.presenter.server_running:
            self.presenter.run_server()
        else:
            self.presenter.stop_server()

    @staticmethod
    def on_configure(canvas):
        canvas.configure(scrollregion=canvas.bbox("all"))

    def canvas_resize(self, event, canvas):
        canvas_width = event.width
        canvas.itemconfig(self.canvas_frame, width=canvas_width)

    def add_list_commands(self, root):
        canvas = tk.Canvas(root, borderwidth=0)
        self.frame = tk.Frame(canvas)
        scrollbar = tk.Scrollbar(root, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        canvas.pack(fill="both", expand=True)
        self.canvas_frame = canvas.create_window((4, 4), window=self.frame, anchor="nw")

        canvas.bind('<Configure>', lambda event, canvas=canvas: self.canvas_resize(event, canvas))
        self.frame.bind("<Configure>", lambda event, canvas=canvas: self.on_configure(canvas))
        self.frame.bind_all("<MouseWheel>", lambda event, canvas=canvas: canvas.yview_scroll(-1 * event.delta, "units"))
        self.canvas = canvas

    @staticmethod
    def clear_text(skill):
        active = '☑' in skill
        skill_without_tick = skill.replace('☑\x1b[32m ', '').replace('\x1b[0m', '').replace('◻', '').strip()
        return skill_without_tick, active

    @staticmethod
    def extract_skill_name(skill):
        installed = '(Installed)' in skill
        return skill.replace('(Installed)', '').replace('(Not Installed)', '').strip(), installed

    @staticmethod
    def remove_emoji(description):
        if not description:
            return ''

        char_list = [description[j] for j in range(len(description)) if ord(description[j]) in range(65536)]
        description = ''
        for char in char_list:
            description = description + char
        return description
