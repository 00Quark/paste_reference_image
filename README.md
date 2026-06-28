# Paste Reference Image

A Blender addon that pastes images directly from your clipboard as a Reference Image in the 3D viewport — no need to save the file first.

Useful when you copy an image from a browser, screenshot something, or Ctrl+C any image and want it instantly as a reference in Blender.

## Features

- Paste any clipboard image as a Reference Image with `Ctrl+Shift+V`
- Supports multiple clipboard sources:
  - **Copy Image** from Chrome / Edge (right-click on any image)
  - **Direct image URL** copied as text (`.png`, `.jpg`, `.webp`, etc.)
  - **HTML clipboard** with `<img src=...>` (auto-downloads the image)
- Spawns the reference in front of the current view, not at world origin
- Optional alignment to the current view angle
- Adjustable size
- Works on Windows, macOS, and Linux

## Compatibility

| Blender | Status |
|---------|--------|
| 5.x | ✅ Tested |
| 4.x | ✅ Should work |
| 3.x | ⚠️ Untested |

## Installation

1. Download `paste_reference_image.py`
2. Open Blender → **Edit → Preferences → Add-ons → Install**
3. Select the `.py` file
4. Enable **Paste Reference Image**

## Usage

### Shortcut
Press `Ctrl+Shift+V` while your mouse is over the 3D viewport.

### N-Panel
Open the sidebar (`N`) → **Reference** tab → click **Paste Reference**.

### Options
| Option | Description |
|--------|-------------|
| Size | Display size of the reference image empty |
| Align to View | Rotates the image to face the current viewport camera |

## Platform Notes

**Windows** — works out of the box. Uses the Blender Python executable to read the clipboard, with a PowerShell fallback. Optionally faster with `pywin32` + `Pillow` installed.

**macOS** — uses `osascript` natively. Install `pngpaste` via Homebrew for better compatibility:
```
brew install pngpaste
```

**Linux** — requires `xclip` (X11) or `wl-paste` (Wayland):
```
sudo apt install xclip
```

