from rich.console import RenderableType
from rich.text import Text
from textual import events
from textual.app import App
from textual.view import messages
from textual.views import DockView
from textual.widgets import Header, Footer, TreeControl, ScrollView, TreeClick
from pytest_fold.utils import Results, MarkedSections


class FoldFooter(Footer):
    # Override default Footer method 'make_key_text' to allow customizations
    def make_key_text(self) -> Text:
        """Create text containing all the keys."""
        text = Text(
            style="bold encircle white on black",
            no_wrap=True,
            overflow="ellipsis",
            justify="center",
            end="",
        )
        for binding in self.app.bindings.shown_keys:
            key_display = (
                binding.key.upper()
                if binding.key_display is None
                else binding.key_display
            )
            hovered = self.highlight_key == binding.key
            key_text = Text.assemble(
                (f" {key_display} ", "reverse" if hovered else "default on default"),
                f" {binding.description} ",
                meta={"@click": f"app.press('{binding.key}')", "key": binding.key},
            )
            text.append_text(key_text)
        return text


class FoldApp(App):
    """
    Textual class inherited from App
    Provides docking and data population for test session headers and results
    """

    async def action_toggle_tree(self, names: list) -> None:
        # self.trees = {child.name: child for child in self.children}
        if type(names) == str:
            names = [names]
        for name in names:
            widget = self.view.named_widgets[
                name
            ]  # <= self here is View; see end of view.py
            widget.visible = not widget.visible  # <= 'visible' is attr on Widget class
            await self.post_message(messages.Layout(self))

    async def on_load(self, event: events.Load) -> None:
        # Populate footer with quit and toggle info
        await self.bind("f", "toggle_tree('fail_tree')", "Toggle Fail  ⁞")
        await self.bind("p", "toggle_tree('pass_tree')", "Toggle Pass  ⁞")
        await self.bind("e", "toggle_tree('error_tree')", "Toggle Error  ⁞")
        await self.bind("m", "toggle_tree('misc_tree')", "Toggle Misc  ⁞")
        await self.bind(
            "a",
            "toggle_tree(['misc_tree', 'error_tree', 'pass_tree', 'fail_tree'])",
            "Toggle All  ⁞",
        )
        await self.bind("q", "quit", "Quit")

        # Get test result sections
        self.test_results = Results()
        self.marked_sections = MarkedSections()
        self.summary_text = (
            Text.from_ansi(self.marked_sections.get_section("LASTLINE")["content"])
            .markup.replace("=", "")
            .strip()
        )

    async def on_mount(self) -> None:
        # Create and dock header and footer widgets
        self.title = self.summary_text
        header1 = Header(style="bold white on black")
        header1.title = self.summary_text
        await self.view.dock(header1, edge="top", size=1)
        footer = FoldFooter()
        await self.view.dock(footer, edge="bottom")

        # Stylize the results-tree section headers
        self.fail_tree = TreeControl(
            Text("FAILED:", style="bold red underline"), {}, name="fail_tree"
        )
        self.pass_tree = TreeControl(
            Text("PASSED:", style="bold green underline"), {}, name="pass_tree"
        )
        self.error_tree = TreeControl(
            Text("ERRORS:", style="bold magenta underline"), {}, name="perror_tree"
        )
        self.misc_tree = TreeControl(
            Text("MISC:", style="bold YELLOW underline"), {}, name="misc_tree"
        )

        for failed in self.test_results.failures:
            await self.fail_tree.add(
                self.fail_tree.root.id,
                Text(failed),
                {"results": self.test_results.failures},
            )
        for errored in self.test_results.errors:
            await self.error_tree.add(
                self.error_tree.root.id,
                Text(errored),
                {"results": self.test_results.errors},
            )
        for passed in self.test_results.passes:
            await self.pass_tree.add(
                self.pass_tree.root.id,
                Text(passed),
                {"results": self.test_results.passes},
            )
        for misc in self.test_results.misc:
            await self.misc_tree.add(
                self.misc_tree.root.id, Text(misc), {"results": self.test_results.misc}
            )
        await self.fail_tree.root.expand()
        await self.pass_tree.root.expand()
        await self.error_tree.root.expand()
        await self.misc_tree.root.expand()

        # Create and dock the results tree
        await self.view.dock(
            ScrollView(self.pass_tree),
            edge="top",
            size=len(self.pass_tree.nodes) + 2,
            # edge="left",
            # size = 25,
            name="pass_tree",
        )
        await self.view.dock(
            ScrollView(self.fail_tree),
            edge="top",
            size=len(self.fail_tree.nodes) + 2,
            # edge="left",
            # size = 25,
            name="fail_tree",
        )
        await self.view.dock(
            ScrollView(self.error_tree),
            edge="top",
            size=len(self.error_tree.nodes) + 2,
            # edge="left",
            # size = 25,
            name="error_tree",
        )
        await self.view.dock(
            ScrollView(self.misc_tree),
            edge="top",
            size=len(self.misc_tree.nodes) + 2,
            # edge="left",
            # size = 25,
            name="misc_tree",
        )

        self.dockview = DockView()
        await self.view.dock(self.dockview)

        # Create and dock the test result ('body') view
        self.body = ScrollView()
        self.body.border = 1
        self.body.border_style = "green"
        await self.dockview.dock(self.body, edge="right")

    async def handle_tree_click(self, message: TreeClick[dict]) -> None:
        label = message.node.label.plain

        # Click the category headers to toggle on/off (future;
        # right now, just ignore those clicks)
        if label == "FAILED:":
            return
        if label == "PASSED:":
            return
        if label == "ERRORS:":
            return

        # Display results when test name is clicked
        self.text = message.node.data.get("results")[label]
        text: RenderableType
        text = Text.from_ansi(self.text)
        await self.body.update(text)


def main():
    app = FoldApp()
    app.run()


if __name__ == "__main__":
    main()
