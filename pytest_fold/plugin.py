import pickle
import pytest
import re
import tempfile
from pathlib import Path

from _pytest.config import Config
from _pytest.main import Session
from _pytest.reports import TestReport
from _pytest._io.terminalwriter import TerminalWriter
from pytest_fold.tuia import main as tui_asciimatics
from pytest_fold.tuit import main as tui_textual
from pytest_fold.utils import (
    TestReportInfo,
    failures_matcher,
    errors_matcher,
    failed_test_marker,
    warnings_summary_matcher,
    summary_matcher,
    lastline_matcher,
    REPORTFILE,
    # OUTFILE,
    # PICKLEFILE,
    # MARKERS,
)

collect_ignore = [
    "setup.py",
    "plugin.py",
]


reports, report_info = [], []


def pytest_addoption(parser):
    group = parser.getgroup("fold")
    group.addoption(
        "--fold", action="store_true", help="fold failed test output sections",
    )
    group.addoption(
        "--fold-tui",
        "--ft",
        action="store",
        default="asciimatics",
        help="specify user interface ('asciimatics' 'a' | 'textual' 't')",
        choices=['asciimatics', 'a', 'textual', 't']
    )
    # group.addoption(
    #     "--fold-now",
    #     "--fn",
    #     action="store_true",
    #     default="False",
    #     help="run TUI from existing results file, bypassing pytest execution",
    # )


# @pytest.hookimpl(hookwrapper=True)
# def pytest_sessionstart(session: Session) -> None:
#     if session.config.getoption("--fold-now") == True:
#         if Path(OUTFILE).exists():
#             pyfold_tui(session.config, session.config.getoption("--fold-tui"))
#             pytest.exit(msg="Quitting TUI")
#         else:
#             pytest.exit(msg="No previous results to display!")
#     yield


def pytest_report_teststatus(report: TestReport, config: Config):
    """Construct list(s) of individial test report/report-info instances"""
    reports.append(report)
    if report.when == "call" and report.outcome == "skipped":
        report_info.append(TestReportInfo(report, report.outcome, report.caplog, report.capstderr, report.capstdout, report.head_line))
    if report.when == "call":
        t = TestReportInfo(report, report.outcome, report.caplog, report.capstderr, report.capstdout, report.head_line)
        report_info_all.append(t)
        if report.outcome == "passed":
            report_info.append(t)
            return


@pytest.hookimpl(trylast=True)
def pytest_configure(config: Config) -> None:
    """
    Write console output to a file for use by TUI
    (part 1; used in conjunction with pytest_unconfigure, below)
    """
    if config.option.fold:
        tr = config.pluginmanager.getplugin("terminalreporter")
        if tr is not None:
            # identify and mark the very first line of terminal output
            try:
                config._pyfoldfirsttime
            except AttributeError:
                config._pyfoldfirsttime = True

            config._pyfoldoutputfile = tempfile.TemporaryFile("wb+")
            oldwrite = tr._tw.write

            # identify and mark each section of results
            def tee_write(s, **kwargs):
                if config._pyfoldfirsttime:
                    config._pyfoldoutputfile.write(
                        (MARKERS["pytest_fold_firstline"] + "\n").encode("utf-8")
                    )
                    config._pyfoldfirsttime = False

                if re.search(errors_matcher, s):
                    config._pyfoldoutputfile.write(
                        (MARKERS["pytest_fold_errors"] + "\n").encode("utf-8")
                    )

                if re.search(failures_matcher, s):
                    config._pyfoldoutputfile.write(
                        (MARKERS["pytest_fold_failures"] + "\n").encode("utf-8")
                    )

                if re.search(failed_test_marker, s):
                    config._pyfoldoutputfile.write(
                        (MARKERS["pytest_fold_failed_test"] + "\n").encode("utf-8")
                    )

                if re.search(warnings_summary_matcher, s):
                    config._pyfoldoutputfile.write(
                        (MARKERS["pytest_fold_warnings_summary"] + "\n").encode("utf-8")
                    )

                if re.search(summary_matcher, s):
                    config._pyfoldoutputfile.write(
                        (MARKERS["pytest_fold_terminal_summary"] + "\n").encode("utf-8")
                    )

                if re.search(lastline_matcher, s):
                    config._pyfoldoutputfile.write(
                        (MARKERS["pytest_fold_lastline"] + "\n").encode("utf-8")
                    )

                # Write this line's text along with its markup info to console
                oldwrite(s, **kwargs)

                # Mark up this line's text by passing it to an instance of TerminalWriter's
                # 'markup' method. Do not pass "flush" to the method or it will throw an error.
                s1 = s
                kwargs.pop("flush") if "flush" in kwargs.keys() else None
                s1 = TerminalWriter().markup(s, **kwargs)

                # Encode the marked up line so it can be written to the config pbject
                if isinstance(s1, str):
                    marked_up = s1.encode("utf-8")
                config._pyfoldoutputfile.write(marked_up)

            tr._tw.write = tee_write


def pytest_unconfigure(config: Config):
    """
    Write console output to a file for use by TUI
    (part 2; used in conjunction with pytest_configure, above)
    """
    # Write the passed test info to file
    with open(PICKLEFILE, "wb") as picklefile:
        pickle.dump(report_info, picklefile)

    # DEBUG ONLY - REMOVE
    with open("report_info_all.pickle", "wb") as picklefile:
        pickle.dump(report_info_all, picklefile)
    with open("reports.pickle", "wb") as picklefile:
        pickle.dump(reports, picklefile)

    # Write the folded terminal output to file
    if hasattr(config, "_pyfoldoutputfile"):
        # get terminal contents, then write file
        config._pyfoldoutputfile.seek(0)
        sessionlog = config._pyfoldoutputfile.read()
        config._pyfoldoutputfile.close()

        # Undo our patching in the terminal reporter.
        config.pluginmanager.getplugin("terminalreporter")

        # write out to file
        with open(OUTFILE, "wb") as outfile:
            outfile.write(sessionlog)

        pyfold_tui(config, config.getoption("--fold-tui"))


def pyfold_tui(config: Config, tui: str = "asciimatics") -> None:
    """
    Final code invocation after Pytest run has completed.
    This method calls the Pyfold TUI to display final results.
    """

    if config.getoption("--fold-now") == True:
        tui_asciimatics() if tui.lower()[0] == "a" else tui_textual()
        return

    # disable capturing while TUI runs to avoid error `redirected stdin is pseudofile, has
    # no fileno()`; adapted from https://githubmemory.com/repo/jsbueno/terminedia/issues/25
    capmanager = config.pluginmanager.getplugin("capturemanager")
    try:
        capmanager.suspend_global_capture(in_=True)
    finally:
        tui_asciimatics() if tui.lower()[0] == "a" else tui_textual()
        capmanager.resume_global_capture()
