#!/usr/bin/env python3
"""Exercise documented desktop behaviour through the event dispatcher."""
from pathlib import Path

from zxtest import boot, render

SHOTS = Path("shots")
EV_PTRMOVE = 1
EV_BTNDOWN = 2
EV_BTNUP = 3
EV_KEY = 4
BUTTON_UP = 0xFF
BUTTON_DOWN = 0xFD


class Gui:
    def __init__(self):
        self.m = boot("")
        SHOTS.mkdir(exist_ok=True)

    def v(self, name):
        return self.m.peek(self.m.sym(name))

    def w(self, name):
        return self.m.peek16(self.m.sym(name))

    def post(self, kind, b=0, c=0):
        self.m.m.a = kind
        self.m.m.b = b
        self.m.m.c = c
        self.m.call("EvPost")
        self.m.call("EvDispatch")

    def move(self, x, y):
        self.m.poke(self.m.sym("PtrX"), x)
        self.m.poke(self.m.sym("PtrY"), y)
        self.post(EV_PTRMOVE, x, y)

    def down(self, x, y):
        self.move(x, y)
        self.m.poke(self.m.sym("Buttons"), BUTTON_DOWN)
        self.post(EV_BTNDOWN, BUTTON_DOWN, 0)

    def up(self, x, y):
        self.move(x, y)
        self.m.poke(self.m.sym("Buttons"), BUTTON_UP)
        self.post(EV_BTNUP, BUTTON_UP, 0)

    def click(self, x, y):
        self.down(x, y)
        self.up(x, y)

    def drag(self, points):
        x, y = points[0]
        self.down(x, y)
        for x, y in points[1:]:
            self.move(x, y)
        self.up(x, y)

    def key(self, value):
        self.post(EV_KEY, value, 0)

    def shot(self, name):
        render(self.m, str(SHOTS / f"gui-{name}.png"))


def check(label, got, want):
    if got != want:
        raise AssertionError(f"{label}: got {got!r}, want {want!r}")
    print(f"ok  {label}")


def test_boot():
    g = Gui()
    check("boot has one window", g.v("WndCount"), 1)
    check("boot has no menu", g.v("MenuOpen"), 0)
    check("boot has no panel", g.v("DlgUp"), 0)
    g.shot("boot")


def test_window_drag_and_resize():
    g = Gui()
    g.drag([(120, 52), (126, 60), (132, 68), (140, 76),
            (148, 84), (156, 96)])
    check("drag x", g.v("WinX"), 12)
    check("drag y", g.v("WinY"), 92)

    g.drag([(236, 160), (228, 154), (216, 146), (204, 138), (196, 132)])
    check("resize width", g.v("WinW"), 13)
    check("resize height", g.v("WinH"), 41)
    small = (g.v("WinW"), g.v("WinH"))
    g.drag([(196, 132), (208, 140), (220, 148), (232, 156), (236, 160)])
    if not (g.v("WinW") > small[0] and g.v("WinH") > small[1]):
        raise AssertionError("resize did not grow both dimensions")
    print("ok  resize grows both dimensions")
    g.shot("drag-resize")


def test_menu_and_settings():
    g = Gui()
    g.click(90, 4)
    check("file menu opens", g.v("MenuOpen"), 2)
    g.click(200, 150)
    check("outside click dismisses menu", g.v("MenuOpen"), 0)

    g.click(20, 4)
    check("desk menu opens", g.v("MenuOpen"), 1)
    g.click(20, 20)
    check("settings opens from menu", g.v("DlgUp"), 1)
    check("settings focus starts first", g.v("PnlFocus"), 0)

    old = g.v("SetInvertY")
    g.key(g.m.sym("KEY_DOWN"))
    g.key(g.m.sym("KEY_ENTER"))
    check("settings keyboard cycles value", g.v("SetInvertY"), old ^ 1)
    g.key(g.m.sym("KEY_ENTER"))
    check("settings value cycles back", g.v("SetInvertY"), old)
    g.shot("settings")


def test_menu_actions():
    g = Gui()
    start = g.v("WndCount")

    g.click(145, 4)
    g.click(145, 12)
    check("view clock menu action", g.v("WndCount"), start + 1)
    check("clock is front", g.w("WinApp"), g.m.sym("AppClock"))

    g.click(196, 4)
    g.click(196, 12)
    check("help keys menu action", g.v("WndCount"), start + 2)
    check("keys is front", g.w("WinApp"), g.m.sym("AppKeys"))

    g.click(90, 4)
    g.click(90, 20)
    check("file open menu action", g.v("WndCount"), start + 3)
    check("commander is front", g.w("WinApp"), g.m.sym("AppCmd"))
    g.shot("menu-actions")


def test_notepad_keys_and_close_guard():
    g = Gui()
    for ch in "HELLO":
        g.key(ord(ch))
    base = g.m.sym("NoteBuf")
    got = bytes(g.m.peek(base + i) for i in range(5))
    check("notepad receives event keys", got, b"HELLO")
    check("notepad cursor advances", g.v("NoteCX"), 5)

    g.key(g.m.sym("KEY_LEFT"))
    g.key(ord("X"))
    got = bytes(g.m.peek(base + i) for i in range(6))
    check("notepad inserts", got, b"HELLXO")

    g.key(g.m.sym("SC_CLOCK"))
    g.key(g.m.sym("SC_NEXT"))
    check("dirty note is front before close", g.w("WinApp"), g.m.sym("AppNote"))
    count = g.v("WndCount")
    g.key(g.m.sym("SC_CLOSE"))
    check("dirty close keeps window pending answer", g.v("WndCount"), count)
    check("dirty close opens save dialogue", g.v("DgDepth"), 1)
    check("dirty close has three answers", g.v("PnlRows"), 5)
    check("dirty close defaults to cancel", g.v("PnlFocus"), 2)
    g.key(g.m.sym("KEY_ENTER"))
    check("cancel keeps dirty window", g.v("WndCount"), count)
    check("cancel closes save dialogue", g.v("DgDepth"), 0)
    g.shot("dirty-close")


def test_desktop_shortcuts_and_arrange():
    g = Gui()
    start = g.v("WndCount")
    g.click(14, 56)
    check("clock desktop shortcut", g.v("WndCount"), start + 1)
    g.click(14, 88)
    check("calendar desktop shortcut", g.v("WndCount"), start + 2)
    g.click(14, 120)
    check("files desktop shortcut", g.v("WndCount"), start + 3)

    count = g.v("WndCount")
    g.key(g.m.sym("SC_CASCADE"))
    check("cascade preserves windows", g.v("WndCount"), count)
    cascade = (g.v("WinX"), g.v("WinY"), g.v("WinW"), g.v("WinH"))
    g.key(g.m.sym("SC_TILE"))
    check("tile preserves windows", g.v("WndCount"), count)
    tiled = (g.v("WinX"), g.v("WinY"), g.v("WinW"), g.v("WinH"))
    if tiled == cascade:
        raise AssertionError("tile left front-window geometry unchanged from cascade")
    print("ok  tile changes arranged geometry")
    g.shot("arranged")


def test_shortcut_windows_and_close():
    g = Gui()
    start = g.v("WndCount")
    g.key(g.m.sym("SC_CLOCK"))
    check("clock shortcut", g.v("WndCount"), start + 1)
    check("clock shortcut focuses clock", g.w("WinApp"), g.m.sym("AppClock"))

    g.key(g.m.sym("SC_NEXT"))
    check("next window changes focus", g.w("WinApp"), g.m.sym("AppNote"))

    g.key(g.m.sym("SC_CALENDAR"))
    check("calendar shortcut", g.v("WndCount"), start + 2)
    check("calendar shortcut focuses calendar", g.w("WinApp"), g.m.sym("AppCal"))

    g.key(g.m.sym("SC_FILES"))
    check("files shortcut", g.v("WndCount"), start + 3)
    check("files shortcut focuses commander", g.w("WinApp"), g.m.sym("AppCmd"))

    g.key(g.m.sym("SC_CLOSE"))
    check("close removes front window", g.v("WndCount"), start + 2)
    g.shot("shortcut-close")



def test_clock_and_calendar_keys():
    g = Gui()
    g.key(g.m.sym("SC_CLOCK"))
    check("clock starts on hours", g.v("ClkField"), 0)
    hour = g.v("ClkH")
    g.key(g.m.sym("KEY_UP"))
    check("clock hour key", g.v("ClkH"), (hour + 1) % 24)
    g.key(g.m.sym("KEY_RIGHT"))
    check("clock selects minutes", g.v("ClkField"), 1)
    minute = g.v("ClkM")
    g.key(g.m.sym("KEY_DOWN"))
    check("clock minute key", g.v("ClkM"), (minute - 1) % 60)

    g.key(g.m.sym("SC_CALENDAR"))
    day = g.v("CalSel")
    g.key(g.m.sym("KEY_RIGHT"))
    check("calendar moves one day", g.v("CalSel"), day + 1)
    g.key(g.m.sym("KEY_DOWN"))
    check("calendar moves one week", g.v("CalSel"), day + 8)
    g.key(g.m.sym("KEY_ENTER"))
    check("calendar sets today day", g.v("TodayD"), g.v("CalSel"))
    check("calendar sets today month", g.v("TodayM"), g.v("CalMonth"))
    check("calendar sets today year", g.v("TodayY"), g.v("CalYear"))
    g.shot("clock-calendar-keys")


def test_commander_and_desktop_setup():
    g = Gui()
    g.key(g.m.sym("SC_FILES"))
    check("commander starts left", g.v("CmdActive"), 0)
    g.key(g.m.sym("KEY_RIGHT"))
    check("commander selects right pane", g.v("CmdActive"), 1)
    g.key(g.m.sym("KEY_LEFT"))
    check("commander returns left pane", g.v("CmdActive"), 0)

    g.key(g.m.sym("SC_DESKTOP"))
    check("desktop setup has eight rows", g.v("PnlRows"), 8)
    check("desktop setup focus starts first", g.v("PnlFocus"), 0)
    present = g.m.peek(g.m.sym("DskTab"))
    g.key(g.m.sym("KEY_ENTER"))
    check("desktop setup toggles note", g.m.peek(g.m.sym("DskTab")), present ^ 1)
    g.key(g.m.sym("KEY_ENTER"))
    check("desktop setup toggles note back", g.m.peek(g.m.sym("DskTab")), present)
    g.shot("commander-desktop")


def test_save_as_panel():
    g = Gui()
    g.key(ord("A"))
    g.key(g.m.sym("SC_SAVEAS"))
    check("save as panel opens", g.v("FmUp"), 1)
    check("save as has three rows", g.v("PnlRows"), 3)
    check("save as starts in name", g.v("PnlFocus"), 1)
    field = bytes(g.m.peek(g.m.sym("FmField") + i) for i in range(4))
    check("save as seeds note name", field, b"NOTE")
    g.key(g.m.sym("KEY_DOWN"))
    g.key(g.m.sym("KEY_ENTER"))
    check("save as closes after save", g.v("FmUp"), 0)
    check("save as reports success", g.v("NoteResult"), 0)
    g.shot("save-as")


def test_multiple_notes_and_about():
    g = Gui()
    start = g.v("WndCount")
    g.key(g.m.sym("SC_NEW"))
    check("new shortcut opens note", g.v("WndCount"), start + 1)
    check("new shortcut focuses note", g.w("WinApp"), g.m.sym("AppNote"))
    g.key(ord("Z"))
    check("new note receives text", g.m.peek(g.m.sym("NoteBuf")), ord("Z"))
    g.key(g.m.sym("SC_NEXT"))
    check("next returns to other note", g.w("WinApp"), g.m.sym("AppNote"))
    check("other note keeps separate text", g.m.peek(g.m.sym("NoteBuf")), ord(" "))
    g.key(g.m.sym("SC_ABOUT"))
    check("about shortcut opens window", g.v("WndCount"), start + 2)
    check("about is front", g.w("WinApp"), g.m.sym("AppAbout"))
    count = g.v("WndCount")
    g.key(g.m.sym("SC_ABOUT"))
    check("second about focuses existing window", g.v("WndCount"), count)
    g.shot("multi-note-about")

def main():
    tests = [
        test_boot,
        test_window_drag_and_resize,
        test_menu_and_settings,
        test_menu_actions,
        test_notepad_keys_and_close_guard,
        test_desktop_shortcuts_and_arrange,
        test_shortcut_windows_and_close,
        test_clock_and_calendar_keys,
        test_commander_and_desktop_setup,
        test_save_as_panel,
        test_multiple_notes_and_about,
    ]
    for test in tests:
        print(f"-- {test.__name__}")
        test()
    print(f"all {len(tests)} gui acceptance groups pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
