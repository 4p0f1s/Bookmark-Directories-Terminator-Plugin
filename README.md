# Bookmark Directories - Terminator Plugin

A keyboard-driven directory navigator for [Terminator](https://gnome-terminator.org/). Bookmark your favourite paths, jump between directories instantly, and navigate your history - all without leaving the keyboard.

![Python](https://img.shields.io/badge/python-3.6%2B-blue)
![GTK](https://img.shields.io/badge/GTK-3-green)
![Terminator](https://img.shields.io/badge/Terminator-plugin-orange)

> 🇬🇧 English | [🇪🇸 Español](README.es.md)

---

## Features

| Feature | Description |
|---------|-------------|
|  **Bookmarks** | Save directories with a custom alias |
|  **Recent** | Last 10 directories visited via the plugin |
|  **Frequent** | Top 10 most-used `cd` targets extracted from bash/zsh history |
|  **Git repos** | Auto-detected repositories highlighted separately |
|  **pushd / popd** | In-memory navigation stack - go deep, come back with one shortcut |
|  **Preview** | Optional inline directory listing when you select an entry |
|  **Smart search** | Prefix → substring → fuzzy, in that priority order |
|  **Language toggle** | Switch the entire UI between English and Spanish from the popup header |

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+B` | Open the directory picker (cd mode) |
| `Ctrl+→` | Open the directory picker (pushd mode - saves current position) |
| `Ctrl+←` | Pop the stack and go back to the previous directory immediately |
| `Enter` | Confirm the selected directory (cd or pushd depending on mode) |
| Double-click | Same as Enter |

---

## Language Toggle

The popup header includes two flag buttons: **🇬🇧** for English and **🇪🇸** for Spanish. Clicking either one instantly translates the entire interface - all labels, tooltips, placeholders, section headers, and dialog buttons. The selected language is remembered for the rest of the session.

---

## pushd / popd

The plugin implements a lightweight navigation stack, similar to the shell built-ins `pushd` and `popd`:

- **`Ctrl+→` (pushd)** - Saves your current directory onto the stack, then navigates to the one you select. The popup title changes to `→ pushd` so you always know which mode you are in.
- **`Ctrl+←` (popd)** - Instantly navigates back to the last saved directory and removes it from the stack. No popup, no noise.

The stack is **per-session** (in memory only). It resets when Terminator is closed, which keeps behaviour predictable.

```
You are at:  ~/projects/web
Ctrl+→  →  select ~/projects/api        stack: [~/projects/web]
Ctrl+→  →  select /var/log              stack: [~/projects/web, ~/projects/api]
Ctrl+←                                  → back to ~/projects/api
Ctrl+←                                  → back to ~/projects/web
Ctrl+←                                  → stack empty, nothing happens
```

---

## Smart Search

The search box filters all sections simultaneously using a three-tier strategy:

1. **Prefix match** - `pro` finds `projects` (highest priority)
2. **Substring match** - `cts` finds `projects`
3. **Fuzzy match** - `prjs` finds `projects` (all characters present in order)

Results stop at the first tier that produces matches, so prefix hits always appear before weaker fuzzy results.

---

## Sections

| Section | Source |
|---------|--------|
| **Stack** | Directories currently on the pushd stack |
| **Bookmarks** | Your saved favourites with aliases |
| **Recent** | Last 10 directories navigated via the plugin (current session) |
| **Frequent** | Top 10 from `~/.bash_history` / `~/.zsh_history` `cd` commands |
| **Git Repos** | Repos found under `~`, `~/projects`, `~/dev`, `~/code`, `~/workspace`, `~/repos`, `~/src` |

---

## Installation

```bash
cp bookmark_directories.py ~/.config/terminator/plugins/
```

1. Open Terminator
2. Go to **Preferences → Plugins**
3. Enable **BookmarkDirectoriesPlugin**
4. Restart Terminator

---

## Managing Bookmarks

- **Save here** button (top-right of the popup) - saves the current directory with an optional alias. Includes a folder browser (`...`).
- **Delete** button - removes the selected bookmark (only active when a Bookmarks entry is selected).
- Bookmarks are stored in `~/.config/terminator/bm_bookmarks.json` and persist across sessions.

---

## Preview Panel

When enabled, selecting any entry shows the directory contents in a small panel at the bottom of the popup:

-  directories
-  symbolic links
-  executable files

Toggle with the **👁** button in the popup header. The preference persists in `~/.config/terminator/bm_config.json`.

---

## Configuration Files

| File | Contents |
|------|----------|
| `~/.config/terminator/bm_bookmarks.json` | Saved bookmarks |
| `~/.config/terminator/bm_config.json` | Preferences (`show_preview`) |

---

## Requirements

- Python 3.6+
- Terminator with plugin support
- GTK 3
- No external dependencies
