import tkinter as tk
from tkinter import ttk
from typing import Any

from guilib.pages import Page


class ScrollablePage(Page):
    def __init__(self, root: tk.Misc, sticky: str = "NSEW"):
        Page.__init__(self, root, sticky)

        parent = super().frame  # the Page full frame

        canvas = tk.Canvas(parent, borderwidth=0)

        def _yview(*args: Any) -> None:
            canvas.yview(*args) # type: ignore

        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=_yview)

        # This is the frame we want `frame()` to return
        self.__scrollable_frame = ttk.Frame(canvas)

        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Create window inside canvas
        self._window = canvas.create_window((0, 0), window=self.__scrollable_frame, anchor="nw")


        # Resize canvas and content (scrollable frame) to mimic sticky behavior for scrollable frame
        # Horizontal resizing

        def _on_content_configure_x(event: Any) -> None:
            canvas.config(width=self.__scrollable_frame.winfo_reqwidth())
        self.__scrollable_frame.bind("<Configure>", _on_content_configure_x, add="+")
        def _on_content_configure_y(event: Any) -> None:
            canvas.config(height=self.__scrollable_frame.winfo_reqheight())
        self.__scrollable_frame.bind("<Configure>", _on_content_configure_y, add="+")

 
        def _on_canvas_configure_x(event: Any) -> None:
            canvas.itemconfig(self._window, width=canvas.winfo_width())
        canvas.bind("<Configure>", _on_canvas_configure_x, add="+")


        
        # Vertical resizing
        
        
        # keep canvas scrollregion in sync with contents
        def _on_configure(event: Any) -> None:
            canvas.configure(scrollregion=canvas.bbox("all"))

        self.__scrollable_frame.bind("<Configure>", _on_configure, add="+")
        canvas.bind("<Configure>", _on_configure, add="+")

        # # DEBUG: print sizes
        # def _print_sizes(event: Any) -> None:

        #     if "e" in sticky.lower() and "w" in sticky.lower():
        #         print(f"(H stretch) ", end="")
        #     else:
        #         print(f"(H fixed) ", end="")
        #     if "n" in sticky.lower() and "s" in sticky.lower():
        #         print(f"(V stretch) ", end="")
        #     else:
        #         print(f"(V fixed) ", end="")

        #     print(f"canvas: {canvas.winfo_width()}x{canvas.winfo_height()}, content: {self.__scrollable_frame.winfo_width()}x{self.__scrollable_frame.winfo_height()}, request: {canvas.winfo_reqwidth()}x{canvas.winfo_reqheight()}")
        # canvas.bind("<Configure>", _print_sizes, add="+") 
        # self.__scrollable_frame.bind("<Configure>", _print_sizes, add="+")

        # ----- scrolling handlers -----
        # mouse / touch wheel
        def _on_mousewheel(event: Any) -> None:
            # X11: event.num == 4 (up) or 5 (down)
            if hasattr(event, "num") and event.num in (4, 5):
                delta = -1 if event.num == 4 else 1
                canvas.yview_scroll(delta, "units")
            else:
                # Windows/OSX: event.delta is multiple of 120
                delta = int(-1 * (event.delta / 120)) if hasattr(event, "delta") else 0
                if delta:
                    canvas.yview_scroll(delta, "units")

        # drag to scroll (useful on touch devices / pydroid)
        self._drag_start_y: float | None = None

        def _on_button_press(event: Any) -> None:
            # Use root coords so events from child widgets still work
            try:
                y = event.y_root - canvas.winfo_rooty()
            except Exception:
                y = float(event.y)
            self._drag_start_y = float(y)

        def _on_drag(event: Any) -> None:
            if self._drag_start_y is None:
                return
            try:
                current_y = event.y_root - canvas.winfo_rooty()
            except Exception:
                current_y = float(event.y)
            dy = current_y - self._drag_start_y
            bbox = canvas.bbox("all")
            if bbox:
                total = bbox[3] - bbox[1]
                if total > 0:
                    first, _ = canvas.yview() # type: ignore
                    new_first = first - (dy / total)
                    canvas.yview_moveto(max(0.0, min(new_first, 1.0)))
            self._drag_start_y = float(current_y)

        def _on_button_release(event: Any) -> None:
            self._drag_start_y = None

        

        # Note: drag handlers will be bound/unbound on Enter/Leave below
        # using bind_all so clicks on child widgets are captured as well.
        # Bind/unbind global wheel handlers when the pointer enters/leaves
        # the scrollable area. This keeps wheel handling local to the
        # visible scroll region and avoids stale global handlers after
        # pages are hidden/destroyed.
        def _bind_wheel_to_all(event: Any) -> None:
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
            canvas.bind_all("<Button-4>", _on_mousewheel)
            canvas.bind_all("<Button-5>", _on_mousewheel)

        def _unbind_wheel_from_all(event: Any) -> None:
            try:
                canvas.unbind_all("<MouseWheel>")
                canvas.unbind_all("<Button-4>")
                canvas.unbind_all("<Button-5>")
            except Exception:
                pass

        def _bind_drag_handlers(event: Any) -> None:
            # Use bind_all so drag works when pressing on child widgets.
            canvas.bind_all("<ButtonPress-1>", _on_button_press)
            canvas.bind_all("<B1-Motion>", _on_drag)
            canvas.bind_all("<ButtonRelease-1>", _on_button_release)

        def _unbind_drag_handlers(event: Any) -> None:
            try:
                canvas.unbind_all("<ButtonPress-1>")
                canvas.unbind_all("<B1-Motion>")
                canvas.unbind_all("<ButtonRelease-1>")
            except Exception:
                pass

        def _on_enter(event: Any) -> None:
            _bind_wheel_to_all(event)
            _bind_drag_handlers(event)

        def _on_leave(event: Any) -> None:
            _unbind_wheel_from_all(event)
            _unbind_drag_handlers(event)

        canvas.bind("<Enter>", _on_enter)
        self.__scrollable_frame.bind("<Enter>", _on_enter)
        canvas.bind("<Leave>", _on_leave)
        self.__scrollable_frame.bind("<Leave>", _on_leave)
    @property
    def frame(self):
        """Return the inner scrollable frame so callers draw into it."""
        return self.__scrollable_frame