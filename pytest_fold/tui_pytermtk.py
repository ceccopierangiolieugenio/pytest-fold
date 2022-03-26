import platform
import subprocess
import sys
import TermTk as ttk
from TermTk.TTkCore.constant import TTkK
from os import get_terminal_size
from pytest_fold.utils import Results

TERMINAL_SIZE = get_terminal_size()


class TkTui:
    def __init__(self) -> None:
        # Retrieve pytest results and extract summary results
        self.test_results = Results()
        self.summary_results = (
            self.test_results._marked_output.get_section("LAST_LINE")[
                "content"
            ].replace("=", "")
            # .rstrip("\n")
        )
        # Create root TTk object
        self.root = ttk.TTk()

    def create_top_frame(self) -> None:
        self.top_frame = ttk.TTkFrame(
            parent=self.root,
            pos=(0, 0),
            size=(TERMINAL_SIZE.columns - 10, 3),
            border=True,
            # layout=ttk.TTkLayout(),
        )
        self.top_label = ttk.TTkLabel(
            parent=self.top_frame, pos=(0, 0)  # , size=(TERMINAL_SIZE.columns - 10, 3)
        )
        self.top_label.setText(ttk.TTkString(self.summary_results))
        # top_label.setText(summary_results)

    def quit(self) -> None:
        # Quits app and resstores terminal for Windows, Mac, Linux
        ttk.TTkTimer.quitAll()
        if platform.system() == "Windows":
            subprocess.Popen("cls", shell=True).communicate()
        else:  # Linux and Mac
            print("\033c", end="")
        sys.exit()

    def create_quit_button(self) -> None:
        self.quit_button_frame = ttk.TTkFrame(
            parent=self.root,
            pos=(TERMINAL_SIZE.columns - 10, 0),
            size=(10, 3),
            border=True,
            layout=ttk.TTkVBoxLayout(),
        )
        self.quit_button = ttk.TTkButton(parent=self.quit_button_frame, text="Quit")
        self.quit_button.layout()
        self.quit_button.clicked.connect(self.quit)

    def create_main_frame(self):
        # Main frame to hold tab and text widgets
        self.main_frame = ttk.TTkFrame(
            parent=self.root,
            pos=(0, 3),
            size=(TERMINAL_SIZE.columns, TERMINAL_SIZE.lines - 3),
            border=False,
            layout=ttk.TTkVBoxLayout(),
        )

    def create_tabs(self, section: str) -> None:
        # Create tabs with results from individual sections
        self.tab_widget = ttk.TTkTabWidget(
            parent=self.main_frame, border=True, height=4
        )

        text = (
            self.test_results._marked_output.get_section("TEST_SESSION_STARTS")[
                "content"
            ]
            + self.test_results._marked_output.get_section("SHORT_TEST_SUMMARY")[
                "content"
            ]
            + "\n"
            + self.test_results._marked_output.get_section("LAST_LINE")["content"]
        )
        tab_label = "Session Summary"
        text_area = ttk.TTkTextEdit(parent=self.tab_widget)
        # text_area.lineWrapMode == TTkK.WidgetWidth
        text_area.setText(text)
        text_areas = {tab_label: text_area}
        self.tab_widget.addTab(text_area, f"  {tab_label}  ")

        text = self.test_results._unmarked_output
        tab_label = "Raw Output"
        text_area = ttk.TTkTextEdit(parent=self.tab_widget)
        text_areas[tab_label] = text_area
        text_area.setText(text)
        self.tab_widget.addTab(text_area, f"  {tab_label}  ")

        text = self.test_results._marked_output.get_section("PASSES_SECTION")[
            "content"
        ]
        tab_label = "Passes Section"
        text_area = ttk.TTkTextEdit(parent=self.tab_widget)
        text_area.setText(text)
        text_areas[tab_label] = text_area
        self.tab_widget.addTab(text_area, f"  {tab_label}  ")

        text = self.test_results._marked_output.get_section("FAILURES_SECTION")[
            "content"
        ]
        tab_label = "Failures Section"
        text_area = ttk.TTkTextEdit(parent=self.tab_widget)
        text_area.setText(text)
        text_areas[tab_label] = text_area
        self.tab_widget.addTab(text_area, f"  {tab_label}  ")

        text = self.test_results._marked_output.get_section("ERRORS_SECTION")[
            "content"
        ]
        tab_label = "Errors Section"
        text_area = ttk.TTkTextEdit(parent=self.tab_widget)
        text_area.setText(text)
        text_areas[tab_label] = text_area
        self.tab_widget.addTab(text_area, f"  {tab_label}  ")

        text = self.test_results._marked_output.get_section("WARNINGS_SUMMARY")[
            "content"
        ]
        tab_label = "Warning"
        text_area = ttk.TTkTextEdit(parent=self.tab_widget)
        text_area.setText(text)
        text_areas[tab_label] = text_area
        self.tab_widget.addTab(text_area, f"  {tab_label}  ")

    def create_result_lists(self, section: str) -> None:
        for result in "Errors", "Passes", "Failures", "Skipped", "Xfails", "Xpasses":
            results_list = ttk.TTkList(
                parent=self.tab_widget,
                # maxWidth=40,
                # minWidth=10,
                selectionMode=ttk.TTkK.MultiSelection,
            )
            for key in eval(f"self.test_results.{result.lower()}.keys()"):
                results_list.addItem(key)
            self.tab_widget.addTab(results_list, f"  {result}  ")


def main():
    tui = TkTui()

    tui.create_top_frame()
    tui.create_quit_button()
    tui.create_main_frame()

    tui.create_tabs("")
    tui.create_result_lists("")

    tui.root.mainloop()


if __name__ == "__main__":
    main()
