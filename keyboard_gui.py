import json
import colorsys
import subprocess
import sys
from pathlib import Path
from tkinter import Canvas, IntVar, PhotoImage, StringVar, Tk, Toplevel, colorchooser, messagebox, ttk

CONFIG_DIRECTORY = Path.home() / ".config" / "predator" / "saved profiles"
CONFIG_DIRECTORY.mkdir(parents=True, exist_ok=True)
LAST_PROFILE_NAME = CONFIG_DIRECTORY / "last_gui_profile.json"

SCRIPT_PATH = Path(__file__).resolve().parent / "facer_rgb.py"
DEFAULT_COLOR = (255, 255, 255)


class KeyboardGUI:
    MODE_NAMES = {
        "0": "Static",
        "1": "Breath",
        "2": "Neon",
        "3": "Wave",
        "4": "Shifting",
        "5": "Zoom",
    }

    QUICK_COLORS = [
        (255, 0, 0),
        (0, 255, 0),
        (0, 0, 255),
        (255, 255, 0),
        (255, 127, 0),
        (255, 255, 255),
    ]

    def __init__(self) -> None:
        self.root = Tk()
        self.root.title("Predator Lighting Studio")
        self.root.geometry("1040x620")

        self.mode = StringVar(value="3")
        self.mode_label = StringVar(value=self._mode_option_label(self.mode.get()))
        self.speed = IntVar(value=4)
        self.brightness = IntVar(value=100)
        self.direction = StringVar(value="1")
        self.zone_mode = StringVar(value="multi")
        self.red = IntVar(value=DEFAULT_COLOR[0])
        self.green = IntVar(value=DEFAULT_COLOR[1])
        self.blue = IntVar(value=DEFAULT_COLOR[2])
        self.profile_name = StringVar(value="")
        self.loaded_profile = StringVar(value="")

        self.zones = {zone: IntVar(value=1) for zone in range(1, 5)}

        self.status = StringVar(value="")
        self.effect_hint = StringVar(value="")

        self._setup_theme()
        self._build_layout()
        self._load_last_settings()
        self._refresh_profile_options()
        self._update_effect_hint()
        self._update_zone_check_state()
        self._update_preview()

    def _setup_theme(self) -> None:
        style = ttk.Style(self.root)
        if "clam" in style.theme_names():
            style.theme_use("clam")

        base_bg = "#1b0f1d"
        accent = "#d21243"
        panel = "#2a1f2e"

        self.root.configure(background=base_bg)

        style.configure("Main.TFrame", background=base_bg)
        style.configure("Panel.TFrame", background=panel)
        style.configure("TLabel", background=panel, foreground="#f6f7fb")
        style.configure("Header.TLabel", background=base_bg, foreground="#f6f7fb", font=("Segoe UI", 16, "bold"))
        style.configure("Accent.TButton", background=accent, foreground="#f6f7fb")
        style.map("Accent.TButton", background=[("active", accent)], foreground=[("disabled", "#c0c0c0")])
        style.configure("Card.TLabelframe", background=panel, foreground="#f6f7fb")
        style.configure("Card.TLabelframe.Label", background=panel, foreground="#f6f7fb", font=("Segoe UI", 10, "bold"))
        style.configure("TNotebook", background=base_bg)
        style.configure("TNotebook.Tab", background=panel, foreground="#f6f7fb")

    def _build_layout(self) -> None:
        main = ttk.Frame(self.root, padding=16, style="Main.TFrame")
        main.grid(row=0, column=0, sticky="nsew")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        header = ttk.Label(main, text="AURA", style="Header.TLabel")
        header.grid(row=0, column=0, sticky="w")

        notebook = ttk.Notebook(main)
        notebook.grid(row=1, column=0, sticky="nsew")

        control_tab = ttk.Frame(notebook, padding=14, style="Main.TFrame")
        notebook.add(control_tab, text="CUSTOMIZE 1")
        notebook.add(ttk.Frame(notebook, style="Main.TFrame"), text="CUSTOMIZE 2")
        notebook.add(ttk.Frame(notebook, style="Main.TFrame"), text="CUSTOMIZE 3")

        control_tab.columnconfigure(0, weight=1)
        control_tab.columnconfigure(1, weight=1)
        control_tab.columnconfigure(2, weight=1)

        left_panel = ttk.Labelframe(control_tab, text="EFFECT SETTINGS", padding=12, style="Card.TLabelframe")
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=(0, 10))
        left_panel.columnconfigure(1, weight=1)

        self._add_effect_controls(left_panel)

        middle_panel = ttk.Labelframe(control_tab, text="COLOR", padding=12, style="Card.TLabelframe")
        middle_panel.grid(row=0, column=1, sticky="nsew", padx=10, pady=(0, 10))
        middle_panel.columnconfigure(0, weight=1)

        self._add_color_controls(middle_panel)

        right_panel = ttk.Labelframe(control_tab, text="KEYBOARD PREVIEW", padding=12, style="Card.TLabelframe")
        right_panel.grid(row=0, column=2, sticky="nsew", padx=(10, 0), pady=(0, 10))
        right_panel.columnconfigure(0, weight=1)

        self._add_preview(right_panel)

        action_panel = ttk.Labelframe(control_tab, text="PROFILE", padding=12, style="Card.TLabelframe")
        action_panel.grid(row=1, column=0, columnspan=3, sticky="ew")
        action_panel.columnconfigure(1, weight=1)

        self._add_profile_controls(action_panel)

        status_label = ttk.Label(control_tab, textvariable=self.status, foreground="#7ef29d", background="#2a1f2e")
        status_label.grid(row=2, column=0, columnspan=3, sticky="w", pady=(8, 0))

    def _add_effect_controls(self, parent: ttk.Labelframe) -> None:
        ttk.Label(parent, text="Brightness").grid(row=0, column=0, sticky="w")
        brightness_scale = ttk.Scale(parent, variable=self.brightness, from_=0, to=100, orient="horizontal", command=self._on_slider_move)
        brightness_scale.grid(row=0, column=1, sticky="ew", pady=4)
        ttk.Label(parent, textvariable=self.brightness, width=4).grid(row=0, column=2, sticky="e", padx=(6, 0))

        ttk.Label(parent, text="Zone mode").grid(row=1, column=0, sticky="w")
        zone_mode_box = ttk.Combobox(parent, textvariable=self.zone_mode, state="readonly", values=["multi", "whole"])
        zone_mode_box.grid(row=1, column=1, sticky="ew", pady=4)
        zone_mode_box.bind("<<ComboboxSelected>>", self._toggle_zone_mode)

        ttk.Label(parent, text="Effect").grid(row=2, column=0, sticky="w")
        mode_box = ttk.Combobox(
            parent,
            textvariable=self.mode_label,
            state="readonly",
            values=[self._mode_option_label(mode_id) for mode_id in self.MODE_NAMES],
        )
        mode_box.grid(row=2, column=1, sticky="ew", pady=4)
        mode_box.bind("<<ComboboxSelected>>", self._on_mode_change)

        ttk.Label(parent, text="Direction").grid(row=3, column=0, sticky="w")
        direction_box = ttk.Combobox(parent, textvariable=self.direction, state="readonly", values=["1", "2"])
        direction_box.grid(row=3, column=1, sticky="ew", pady=4)
        direction_box.bind("<<ComboboxSelected>>", lambda _event: self._update_preview())

        ttk.Label(parent, text="Speed").grid(row=4, column=0, sticky="w")
        speed_scale = ttk.Scale(parent, variable=self.speed, from_=0, to=9, orient="horizontal", command=self._on_slider_move)
        speed_scale.grid(row=4, column=1, sticky="ew", pady=4)
        ttk.Label(parent, textvariable=self.speed, width=4).grid(row=4, column=2, sticky="e", padx=(6, 0))

        ttk.Label(parent, textvariable=self.effect_hint, wraplength=280, foreground="#c9c9d1", background="#2a1f2e").grid(
            row=5,
            column=0,
            columnspan=3,
            sticky="w",
            pady=(6, 2),
        )

    def _add_color_controls(self, parent: ttk.Labelframe) -> None:
        palette_frame = ttk.Frame(parent, style="Panel.TFrame")
        palette_frame.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        for idx in range(len(self.QUICK_COLORS)):
            palette_frame.columnconfigure(idx, weight=1)

        for idx, rgb in enumerate(self.QUICK_COLORS):
            hex_color = self._rgb_to_hex(rgb)
            btn = ttk.Button(
                palette_frame,
                text="",
                command=lambda val=rgb: self._set_palette_color(val),
                style="Accent.TButton",
                width=2,
            )
            btn.grid(row=0, column=idx, padx=2, sticky="ew")
            btn.configure(style=self._make_color_style(hex_color))

        self.color_display = ttk.Label(
            parent,
            text=self._format_color_label(),
            relief="sunken",
            padding=8,
            anchor="center",
            background="#2a1f2e",
        )
        self.color_display.grid(row=1, column=0, sticky="ew")

        ttk.Button(parent, text="Advanced picker", command=self._open_color_picker, style="Accent.TButton").grid(
            row=2, column=0, sticky="ew", pady=(10, 0)
        )

    def _add_preview(self, parent: ttk.Labelframe) -> None:
        self.preview_canvas = Canvas(parent, width=440, height=200, background="#120a14", highlightthickness=0)
        self.preview_canvas.grid(row=0, column=0, sticky="ew")

        zones_frame = ttk.Frame(parent, style="Panel.TFrame")
        zones_frame.grid(row=1, column=0, sticky="ew", pady=(10, 0))
        ttk.Label(zones_frame, text="Zones (static mode)").grid(row=0, column=0, sticky="w")
        self.zone_checkbuttons = {}
        for idx, zone in enumerate(self.zones, start=1):
            check = ttk.Checkbutton(
                zones_frame,
                text=str(zone),
                variable=self.zones[zone],
                command=self._update_preview,
            )
            check.grid(row=0, column=idx, padx=4)
            self.zone_checkbuttons[zone] = check

        ttk.Button(parent, text="APPLY", command=self._apply_settings, style="Accent.TButton").grid(
            row=2, column=0, sticky="ew", pady=(14, 0)
        )

    def _add_profile_controls(self, parent: ttk.Labelframe) -> None:
        ttk.Label(parent, text="Save as profile").grid(row=0, column=0, sticky="w")
        entry = ttk.Entry(parent, textvariable=self.profile_name)
        entry.grid(row=0, column=1, sticky="ew", padx=6)
        ttk.Button(parent, text="Save", command=self._save_profile, style="Accent.TButton").grid(row=0, column=2, sticky="e")

        ttk.Label(parent, text="Load profile").grid(row=1, column=0, sticky="w", pady=(6, 0))
        self.profile_selector = ttk.Combobox(parent, textvariable=self.loaded_profile, state="readonly")
        self.profile_selector.grid(row=1, column=1, sticky="ew", padx=6, pady=(6, 0))
        ttk.Button(parent, text="Load", command=self._load_selected_profile).grid(row=1, column=2, sticky="e", pady=(6, 0))

    def _on_slider_move(self, _value: str) -> None:
        self._update_preview()

    def _mode_option_label(self, mode_id: str) -> str:
        return f"{mode_id} - {self.MODE_NAMES.get(mode_id, 'Unknown')}"

    def _on_mode_change(self, _event: object) -> None:
        selected = self.mode_label.get().split(" - ", maxsplit=1)[0]
        if selected in self.MODE_NAMES:
            self.mode.set(selected)
        self._update_effect_hint()
        self._update_preview()

    def _toggle_zone_mode(self, _event: object) -> None:
        if self.zone_mode.get() == "whole":
            for var in self.zones.values():
                var.set(1)
        self._update_zone_check_state()
        self._update_preview()

    def _update_zone_check_state(self) -> None:
        state = "!disabled" if self.zone_mode.get() == "multi" else "disabled"
        for zone, widget in getattr(self, "zone_checkbuttons", {}).items():
            widget.state([state])
            if state == "disabled":
                self.zones[zone].set(1)

    def _set_palette_color(self, rgb: tuple[int, int, int]) -> None:
        self.red.set(rgb[0])
        self.green.set(rgb[1])
        self.blue.set(rgb[2])
        self._update_color_display()

    def _open_color_picker(self) -> None:
        dialog = Toplevel(self.root)
        dialog.title("Wybierz kolor")
        dialog.grab_set()
        dialog.resizable(False, False)

        preview_frame = ttk.Frame(dialog, padding=10, style="Main.TFrame")
        preview_frame.grid(row=0, column=0, sticky="nsew")

        ttk.Label(preview_frame, text="Podgląd", style="Header.TLabel").grid(row=0, column=0, sticky="w")
        preview = ttk.Label(
            preview_frame,
            width=20,
            padding=10,
            relief="sunken",
            background=self._current_color_hex(),
            text=self._format_color_label(),
            anchor="center",
        )
        preview.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(6, 10))

        hex_var = StringVar(value=self._current_color_hex())
        ttk.Label(preview_frame, text="HEX:").grid(row=2, column=0, sticky="w")
        hex_entry = ttk.Entry(preview_frame, textvariable=hex_var, width=10)
        hex_entry.grid(row=2, column=1, sticky="e")

        palette_frame = ttk.Frame(preview_frame, padding=(0, 10, 0, 0), style="Panel.TFrame")
        palette_frame.grid(row=3, column=0, columnspan=2, sticky="ew")

        colors = self._rich_palette()
        columns = 10
        for idx, color in enumerate(colors):
            row, col = divmod(idx, columns)
            swatch = ttk.Button(
                palette_frame,
                width=2,
                command=lambda c=color: self._apply_dialog_color(c, preview, hex_var),
            )
            swatch.grid(row=row, column=col, padx=1, pady=1, sticky="ew")
            swatch_style = self._make_color_style(color)
            swatch.configure(style=swatch_style)

        gradient_frame = ttk.Frame(preview_frame, padding=(0, 10, 0, 0), style="Panel.TFrame")
        gradient_frame.grid(row=4, column=0, columnspan=2)

        gradient_canvas = Canvas(gradient_frame, width=220, height=160, highlightthickness=1, highlightbackground="#555")
        gradient_canvas.grid(row=0, column=0)
        gradient_image = self._build_gradient_image(220, 160)
        gradient_canvas.create_image(0, 0, anchor="nw", image=gradient_image)

        def pick_from_gradient(event: object) -> None:
            x, y = event.x, event.y
            color = self._color_from_gradient(x, y, 220, 160)
            self._apply_dialog_color(color, preview, hex_var)

        gradient_canvas.bind("<Button-1>", pick_from_gradient)
        gradient_canvas.image = gradient_image  # type: ignore[attr-defined]

        button_frame = ttk.Frame(preview_frame, padding=(0, 10, 0, 0), style="Panel.TFrame")
        button_frame.grid(row=5, column=0, columnspan=2, sticky="ew")
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)

        def apply_and_close() -> None:
            self._set_hex_color(hex_var.get())
            dialog.destroy()

        def cancel() -> None:
            dialog.destroy()

        ttk.Button(button_frame, text="Anuluj", command=cancel).grid(row=0, column=0, sticky="ew", padx=(0, 4))
        ttk.Button(button_frame, text="Wybierz", command=apply_and_close, style="Accent.TButton").grid(
            row=0, column=1, sticky="ew", padx=(4, 0)
        )

    def _apply_dialog_color(self, color_hex: str, preview: ttk.Label, hex_var: StringVar) -> None:
        hex_var.set(color_hex)
        preview.configure(background=color_hex, text=self._format_color_label_from_hex(color_hex))

    def _format_color_label_from_hex(self, color_hex: str) -> str:
        r, g, b = self._hex_to_rgb(color_hex)
        return f"RGB: {r}, {g}, {b}"

    def _set_hex_color(self, hex_color: str) -> None:
        try:
            r, g, b = self._hex_to_rgb(hex_color)
        except ValueError:
            messagebox.showwarning("Kolor", "Podano nieprawidłowy kolor HEX.")
            return
        self.red.set(r)
        self.green.set(g)
        self.blue.set(b)
        self._update_color_display()

    def _hex_to_rgb(self, hex_color: str) -> tuple[int, int, int]:
        color = hex_color.lstrip("#")
        if len(color) != 6:
            raise ValueError("Invalid hex length")
        r = int(color[0:2], 16)
        g = int(color[2:4], 16)
        b = int(color[4:6], 16)
        return r, g, b

    def _rich_palette(self) -> list[str]:
        return [
            "#f44336",
            "#e91e63",
            "#9c27b0",
            "#673ab7",
            "#3f51b5",
            "#2196f3",
            "#03a9f4",
            "#00bcd4",
            "#009688",
            "#4caf50",
            "#8bc34a",
            "#cddc39",
            "#ffeb3b",
            "#ffc107",
            "#ff9800",
            "#ff5722",
            "#795548",
            "#9e9e9e",
            "#607d8b",
            "#ffffff",
            "#000000",
            "#c62828",
            "#ad1457",
            "#6a1b9a",
            "#4527a0",
            "#283593",
            "#1565c0",
            "#0277bd",
            "#00838f",
            "#00695c",
            "#2e7d32",
            "#558b2f",
            "#9e9d24",
            "#f9a825",
            "#ff8f00",
            "#ef6c00",
            "#d84315",
            "#4e342e",
            "#616161",
            "#37474f",
            "#fce4ec",
            "#f3e5f5",
            "#e8eaf6",
            "#e3f2fd",
            "#e0f7fa",
            "#e0f2f1",
            "#e8f5e9",
            "#f1f8e9",
            "#f9fbe7",
            "#fffde7",
            "#fff8e1",
            "#fff3e0",
            "#fbe9e7",
            "#efebe9",
            "#fafafa",
            "#eceff1",
            "#b71c1c",
            "#880e4f",
            "#4a148c",
            "#311b92",
            "#1a237e",
            "#0d47a1",
            "#01579b",
            "#006064",
            "#004d40",
            "#1b5e20",
            "#33691e",
            "#827717",
            "#f57f17",
            "#ff6f00",
            "#e65100",
            "#bf360c",
            "#3e2723",
            "#212121",
            "#263238",
        ]

    def _build_gradient_image(self, width: int, height: int) -> PhotoImage:
        gradient = PhotoImage(width=width, height=height)
        for x in range(width):
            hue = x / width
            for y in range(height):
                saturation = 1
                value = 1 - (y / height)
                r, g, b = colorsys.hsv_to_rgb(hue, saturation, value)
                gradient.put(self._rgb_to_hex((int(r * 255), int(g * 255), int(b * 255))), (x, y))
        return gradient

    def _color_from_gradient(self, x: int, y: int, width: int, height: int) -> str:
        x = max(0, min(width - 1, x))
        y = max(0, min(height - 1, y))
        hue = x / width
        saturation = 1
        value = 1 - (y / height)
        r, g, b = colorsys.hsv_to_rgb(hue, saturation, value)
        return self._rgb_to_hex((int(r * 255), int(g * 255), int(b * 255)))

    def _current_color_hex(self) -> str:
        return self._rgb_to_hex((self.red.get(), self.green.get(), self.blue.get()))

    def _rgb_to_hex(self, rgb: tuple[int, int, int]) -> str:
        return "#%02x%02x%02x" % rgb

    def _format_color_label(self) -> str:
        return f"RGB: {self.red.get()}, {self.green.get()}, {self.blue.get()}"

    def _update_color_display(self) -> None:
        self.color_display.configure(text=self._format_color_label(), background=self._current_color_hex())
        self._update_preview()

    def _update_effect_hint(self) -> None:
        descriptions = {
            "0": "Static allows per-zone color selection.",
            "1": "Breath softly pulses the selected color.",
            "2": "Neon cycles the spectrum automatically.",
            "3": "Wave sweeps colors across the board.",
            "4": "Shifting rotates through your chosen color.",
            "5": "Zoom radiates the color outward.",
        }
        self.effect_hint.set(descriptions.get(self.mode.get(), ""))

    def _update_preview(self) -> None:
        if not hasattr(self, "preview_canvas"):
            return

        self.preview_canvas.delete("all")
        total_width = 420
        zone_width = total_width // 4
        height = 120
        x_offset = 10
        y_offset = 30

        for idx, zone in enumerate(self.zones, start=0):
            x1 = x_offset + idx * zone_width
            x2 = x1 + zone_width - 6
            y1 = y_offset
            y2 = y_offset + height
            fill_color = self._current_color_hex() if self.zones[zone].get() else "#2f2f3a"
            if self.mode.get() != "0":
                if self.mode.get() in {"1", "4", "5"}:
                    fill_color = self._current_color_hex()
                else:
                    fill_color = "#6b1a2d"
            self.preview_canvas.create_rectangle(x1, y1, x2, y2, fill=fill_color, outline="#3a3a46", width=2)
            self.preview_canvas.create_text((x1 + x2) / 2, y1 + height / 2, text=str(zone), fill="#f6f7fb", font=("Segoe UI", 14, "bold"))

        brightness_text = f"Brightness: {self.brightness.get()}% | Speed: {self.speed.get()}"
        self.preview_canvas.create_text(
            total_width / 2 + x_offset,
            y_offset - 12,
            text=brightness_text,
            fill="#c0c0c8",
            font=("Segoe UI", 10, "bold"),
        )

        direction_text = "Direction: →" if self.direction.get() == "2" else "Direction: ←"
        self.preview_canvas.create_text(
            total_width / 2 + x_offset,
            y_offset + height + 16,
            text=f"Mode: {self.MODE_NAMES.get(self.mode.get(), '')} | {direction_text}",
            fill="#c0c0c8",
            font=("Segoe UI", 10),
        )

    def _apply_settings(self) -> None:
        try:
            for command in self._build_commands():
                subprocess.run(command, check=True)
            self.status.set("Ustawienia zastosowane.")
            self._save_last_profile()
        except subprocess.CalledProcessError as exc:
            self.status.set("Błąd podczas stosowania ustawień.")
            messagebox.showerror("Błąd", f"Nie udało się zastosować ustawień: {exc}")

    def _build_commands(self) -> list[list[str]]:
        base_args = [
            sys.executable,
            str(SCRIPT_PATH),
            "-m",
            self.mode.get(),
            "-s",
            str(self.speed.get()),
            "-b",
            str(self.brightness.get()),
            "-d",
            self.direction.get(),
            "-cR",
            str(self.red.get()),
            "-cG",
            str(self.green.get()),
            "-cB",
            str(self.blue.get()),
        ]
        if self.mode.get() == "0":
            selected_zones = [zone for zone, enabled in self.zones.items() if enabled.get()]
            if not selected_zones or self.zone_mode.get() == "whole":
                selected_zones = [1, 2, 3, 4]
            return [base_args + ["-z", str(zone)] for zone in selected_zones]
        return [base_args]

    def _save_profile(self) -> None:
        name = self.profile_name.get().strip()
        if not name:
            messagebox.showwarning("Profil", "Podaj nazwę profilu do zapisania.")
            return
        self._write_profile(CONFIG_DIRECTORY / f"{name}.json")
        self.profile_name.set("")
        self.status.set(f"Zapisano profil '{name}'.")
        self._refresh_profile_options()

    def _save_last_profile(self) -> None:
        self._write_profile(LAST_PROFILE_NAME)

    def _write_profile(self, path: Path) -> None:
        data = {
            "mode": self.mode.get(),
            "speed": self.speed.get(),
            "brightness": self.brightness.get(),
            "direction": self.direction.get(),
            "zone_mode": self.zone_mode.get(),
            "red": self.red.get(),
            "green": self.green.get(),
            "blue": self.blue.get(),
            "zones": {str(zone): var.get() for zone, var in self.zones.items()},
        }
        with open(path, "w", encoding="utf-8") as profile_file:
            json.dump(data, profile_file, indent=4)

    def _load_selected_profile(self) -> None:
        name = self.loaded_profile.get()
        if not name:
            return
        self._load_profile(CONFIG_DIRECTORY / f"{name}.json")
        self.status.set(f"Wczytano profil '{name}'.")

    def _load_last_settings(self) -> None:
        if LAST_PROFILE_NAME.exists():
            self._load_profile(LAST_PROFILE_NAME)

    def _load_profile(self, path: Path) -> None:
        try:
            with open(path, "r", encoding="utf-8") as profile_file:
                data = json.load(profile_file)
        except FileNotFoundError:
            messagebox.showwarning("Profil", f"Nie znaleziono pliku {path}.")
            return

        self.mode.set(str(data.get("mode", self.mode.get())))
        self.mode_label.set(self._mode_option_label(self.mode.get()))
        self.speed.set(int(data.get("speed", self.speed.get())))
        self.brightness.set(int(data.get("brightness", self.brightness.get())))
        self.direction.set(str(data.get("direction", self.direction.get())))
        self.zone_mode.set(str(data.get("zone_mode", self.zone_mode.get())))
        self.red.set(int(data.get("red", DEFAULT_COLOR[0])))
        self.green.set(int(data.get("green", DEFAULT_COLOR[1])))
        self.blue.set(int(data.get("blue", DEFAULT_COLOR[2])))

        zones_data = data.get("zones", {})
        for zone, var in self.zones.items():
            var.set(int(zones_data.get(str(zone), 1)))

        self._update_color_display()
        self._update_effect_hint()
        self._toggle_zone_mode(None)

    def _refresh_profile_options(self) -> None:
        profiles = sorted([p.stem for p in CONFIG_DIRECTORY.glob("*.json") if p.is_file()])
        self.profile_selector.configure(values=profiles)
        if profiles:
            self.profile_selector.current(0)

    def _make_color_style(self, hex_color: str) -> str:
        style_name = f"Color{hex_color.replace('#', '')}.TButton"
        style = ttk.Style(self.root)
        style.configure(style_name, background=hex_color, foreground="#0f0f0f")
        style.map(style_name, background=[("active", hex_color)])
        return style_name

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    gui = KeyboardGUI()
    gui.run()


if __name__ == "__main__":
    main()