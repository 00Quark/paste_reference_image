bl_info = {
    "name": "Paste Reference Image",
    "author": "00Quark",
    "version": (2, 5, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > Reference | Shortcut: Ctrl+Shift+V",
    "description": "Pastes image from clipboard as a Reference Image in the 3D viewport",
    "category": "3D View",
}

import bpy
import os
import sys
import tempfile
import time


# ─────────────────────────────────────────────
#  Download from URL
# ─────────────────────────────────────────────

def download_image_from_url(url):
    try:
        import urllib.request
        headers = {"User-Agent": "Mozilla/5.0"}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            content_type = resp.headers.get("Content-Type", "")
            if not any(t in content_type for t in ("image", "octet-stream")):
                return None
            data = resp.read()
        ext = ".png"
        if "jpeg" in content_type or "jpg" in content_type:
            ext = ".jpg"
        elif "webp" in content_type:
            ext = ".webp"
        elif "gif" in content_type:
            ext = ".gif"
        tmp = tempfile.NamedTemporaryFile(suffix=ext, delete=False)
        tmp.write(data)
        tmp.close()
        return tmp.name
    except Exception:
        return None


def extract_url_from_html(html_text):
    import re
    m = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', html_text, re.IGNORECASE)
    if m:
        return m.group(1)
    m = re.search(r'https?://[^\s"\'<>]+\.(?:png|jpg|jpeg|webp|gif|bmp)', html_text, re.IGNORECASE)
    if m:
        return m.group(0)
    return None


# ─────────────────────────────────────────────
#  Windows clipboard
# ─────────────────────────────────────────────

def _clipboard_windows():
    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    tmp.close()
    out = tmp.name

    py_lines = [
        "import sys, os",
        "out = sys.argv[1]",
        "saved = False",
        "try:",
        "    import win32clipboard",
        "    from PIL import Image",
        "    import io",
        "    CF_PNG = 0",
        "    try:",
        "        CF_PNG = win32clipboard.RegisterClipboardFormat('PNG')",
        "    except Exception:",
        "        pass",
        "    win32clipboard.OpenClipboard()",
        "    try:",
        "        if CF_PNG and win32clipboard.IsClipboardFormatAvailable(CF_PNG):",
        "            data = win32clipboard.GetClipboardData(CF_PNG)",
        "            img = Image.open(io.BytesIO(data))",
        "            img.save(out, 'PNG')",
        "            saved = True",
        "        elif win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_DIB):",
        "            data = win32clipboard.GetClipboardData(win32clipboard.CF_DIB)",
        "            img = Image.open(io.BytesIO(data))",
        "            img.save(out, 'PNG')",
        "            saved = True",
        "        elif win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_DIBV5):",
        "            data = win32clipboard.GetClipboardData(win32clipboard.CF_DIBV5)",
        "            img = Image.open(io.BytesIO(data))",
        "            img.save(out, 'PNG')",
        "            saved = True",
        "    finally:",
        "        win32clipboard.CloseClipboard()",
        "except Exception:",
        "    pass",
        "if not saved:",
        "    try:",
        "        import tkinter as tk",
        "        from PIL import ImageGrab",
        "        root = tk.Tk()",
        "        root.withdraw()",
        "        img = ImageGrab.grabclipboard()",
        "        if img is not None:",
        "            img.save(out, 'PNG')",
        "            saved = True",
        "        root.destroy()",
        "    except Exception:",
        "        pass",
        "sys.exit(0 if saved and os.path.getsize(out) > 0 else 1)",
    ]

    py_script = "\n".join(py_lines)
    py_tmp = tempfile.NamedTemporaryFile(suffix=".py", mode="w", encoding="utf-8", delete=False)
    py_tmp.write(py_script)
    py_tmp.close()

    python_exe = sys.executable
    ret = os.system('"' + python_exe + '" "' + py_tmp.name + '" "' + out + '" >nul 2>&1')
    try:
        os.unlink(py_tmp.name)
    except Exception:
        pass

    if ret == 0 and os.path.exists(out) and os.path.getsize(out) > 0:
        return out

    # PowerShell fallback
    ps_lines = [
        "Add-Type -AssemblyName System.Windows.Forms",
        "$out = '" + out.replace("\\", "\\\\") + "'",
        "$img = [System.Windows.Forms.Clipboard]::GetImage()",
        "if ($img -ne $null) {",
        "    $img.Save($out, [System.Drawing.Imaging.ImageFormat]::Png)",
        "    exit 0",
        "}",
        "exit 1",
    ]
    ps_script = "\n".join(ps_lines)
    ps_tmp = tempfile.NamedTemporaryFile(suffix=".ps1", mode="w", encoding="utf-8", delete=False)
    ps_tmp.write(ps_script)
    ps_tmp.close()

    ret2 = os.system('powershell -ExecutionPolicy Bypass -File "' + ps_tmp.name + '" >nul 2>&1')
    try:
        os.unlink(ps_tmp.name)
    except Exception:
        pass

    if ret2 == 0 and os.path.exists(out) and os.path.getsize(out) > 0:
        return out

    try:
        os.unlink(out)
    except Exception:
        pass

    return _clipboard_windows_html_url()


def _clipboard_windows_html_url():
    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    tmp.close()
    out = tmp.name.replace("\\", "\\\\")

    ps_lines = [
        "Add-Type -AssemblyName System.Windows.Forms",
        "$out = '" + out + "'",
        "$dataObj = [System.Windows.Forms.Clipboard]::GetDataObject()",
        "if ($dataObj -ne $null) {",
        "    $formats = $dataObj.GetFormats()",
        "    if ($formats -contains 'HTML Format') {",
        "        $html = $dataObj.GetData('HTML Format')",
        "        $m = [regex]::Match($html, 'https?://[^ >\"]+[.](png|jpg|jpeg|webp|gif)')",
        "        if ($m.Success) {",
        "            $url = $m.Value",
        "            Invoke-WebRequest -Uri $url -OutFile $out -UserAgent 'Mozilla/5.0'",
        "            exit 0",
        "        }",
        "    }",
        "    $text = [System.Windows.Forms.Clipboard]::GetText()",
        "    if ($text -match '^https?://.+[.](png|jpg|jpeg|webp|gif)$') {",
        "        Invoke-WebRequest -Uri $text -OutFile $out -UserAgent 'Mozilla/5.0'",
        "        exit 0",
        "    }",
        "}",
        "exit 1",
    ]
    ps_script = "\n".join(ps_lines)
    ps_tmp = tempfile.NamedTemporaryFile(suffix=".ps1", mode="w", encoding="utf-8", delete=False)
    ps_tmp.write(ps_script)
    ps_tmp.close()

    ret = os.system('powershell -ExecutionPolicy Bypass -File "' + ps_tmp.name + '" >nul 2>&1')
    try:
        os.unlink(ps_tmp.name)
    except Exception:
        pass

    if ret == 0 and os.path.exists(tmp.name) and os.path.getsize(tmp.name) > 0:
        return tmp.name

    try:
        os.unlink(tmp.name)
    except Exception:
        pass
    return None


# ─────────────────────────────────────────────
#  macOS clipboard
# ─────────────────────────────────────────────

def _clipboard_macos():
    import subprocess

    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    tmp.close()

    ret = os.system(
        "osascript -e 'set theImage to (the clipboard as \xabclass PNGf\xbb)' "
        "-e 'set fileRef to open for access POSIX file \"" + tmp.name + "\" with write permission' "
        "-e 'write theImage to fileRef' -e 'close access fileRef' 2>/dev/null"
    )
    if ret == 0 and os.path.getsize(tmp.name) > 0:
        return tmp.name

    ret = os.system('pngpaste "' + tmp.name + '" 2>/dev/null')
    if ret == 0 and os.path.getsize(tmp.name) > 0:
        return tmp.name

    os.unlink(tmp.name)

    try:
        result = subprocess.run(
            ["osascript", "-e", "the clipboard as \xabclass HTML\xbb"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            url = extract_url_from_html(result.stdout)
            if url:
                return download_image_from_url(url)
    except Exception:
        pass

    try:
        result = subprocess.run(["pbpaste"], capture_output=True, text=True, timeout=3)
        text = result.stdout.strip()
        if text.startswith("http") and any(
            text.lower().endswith(e) for e in (".png", ".jpg", ".jpeg", ".webp", ".gif")
        ):
            return download_image_from_url(text)
    except Exception:
        pass

    return None


# ─────────────────────────────────────────────
#  Linux clipboard
# ─────────────────────────────────────────────

def _clipboard_linux():
    import subprocess

    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    tmp.close()

    ret = os.system('xclip -selection clipboard -t image/png -o > "' + tmp.name + '" 2>/dev/null')
    if ret == 0 and os.path.getsize(tmp.name) > 0:
        return tmp.name

    ret = os.system('wl-paste --type image/png > "' + tmp.name + '" 2>/dev/null')
    if ret == 0 and os.path.getsize(tmp.name) > 0:
        return tmp.name

    os.unlink(tmp.name)

    try:
        result = subprocess.run(
            ["xclip", "-selection", "clipboard", "-t", "text/html", "-o"],
            capture_output=True, timeout=3
        )
        if result.returncode == 0:
            html = result.stdout.decode("utf-8", errors="ignore")
            url = extract_url_from_html(html)
            if url:
                return download_image_from_url(url)
    except Exception:
        pass

    try:
        result = subprocess.run(
            ["xclip", "-selection", "clipboard", "-o"],
            capture_output=True, text=True, timeout=3
        )
        text = result.stdout.strip()
        if text.startswith("http") and any(
            text.lower().endswith(e) for e in (".png", ".jpg", ".jpeg", ".webp", ".gif")
        ):
            return download_image_from_url(text)
    except Exception:
        pass

    return None


# ─────────────────────────────────────────────
#  Entry point
# ─────────────────────────────────────────────

def get_clipboard_image_path():
    if sys.platform == "win32":
        path = _clipboard_windows()
    elif sys.platform == "darwin":
        path = _clipboard_macos()
    else:
        path = _clipboard_linux()
    return (path, True) if path else (None, False)


# ─────────────────────────────────────────────
#  Get the correct enum value for empty_image_side
# ─────────────────────────────────────────────

def get_double_sided_enum():
    # Blender 5+ uses 'DOUBLE_SIDED', older versions use 'BOTH'
    try:
        props = bpy.types.Object.bl_rna.properties.get("empty_image_side")
        if props:
            enum_items = [i.identifier for i in props.enum_items]
            if 'DOUBLE_SIDED' in enum_items:
                return 'DOUBLE_SIDED'
            if 'BOTH' in enum_items:
                return 'BOTH'
    except Exception:
        pass
    return None


# ─────────────────────────────────────────────
#  Get spawn location from current view
# ─────────────────────────────────────────────

def get_view_location(area_3d):
    import mathutils
    space = area_3d.spaces.active
    r3d = space.region_3d
    view_mat = r3d.view_matrix.inverted()
    forward = view_mat.to_3x3() @ mathutils.Vector((0, 0, -1))
    dist = r3d.view_distance * 0.5
    location = view_mat.translation + forward * dist
    return location


# ─────────────────────────────────────────────
#  Create Reference Image
# ─────────────────────────────────────────────

def create_reference_image(context, filepath, size, align_to_view):
    img = bpy.data.images.load(filepath, check_existing=False)

    area_3d = None
    for area in context.screen.areas:
        if area.type == 'VIEW_3D':
            area_3d = area
            break

    if area_3d is None:
        raise Exception("No 3D viewport found. Click inside the 3D viewport before using the shortcut.")

    region = None
    for r in area_3d.regions:
        if r.type == 'WINDOW':
            region = r
            break

    location = get_view_location(area_3d)

    with context.temp_override(area=area_3d, region=region):
        bpy.ops.object.empty_add(type='IMAGE', location=location)

    obj = context.active_object
    obj.name = "Ref_Clipboard"
    obj.data = img
    obj.empty_display_size = size
    obj.use_empty_image_alpha = True

    # Set double-sided using the correct enum for this Blender version
    side_enum = get_double_sided_enum()
    if side_enum:
        obj.empty_image_side = side_enum

    if align_to_view:
        space = area_3d.spaces.active
        if space and hasattr(space, 'region_3d'):
            obj.rotation_euler = space.region_3d.view_rotation.to_euler()

    return obj


# ─────────────────────────────────────────────
#  Operator
# ─────────────────────────────────────────────

class VIEW3D_OT_paste_reference_image(bpy.types.Operator):
    """Paste clipboard image as a Reference Image in the 3D viewport"""
    bl_idname = "view3d.paste_reference_image"
    bl_label = "Paste Reference Image"
    bl_options = {'REGISTER', 'UNDO'}

    align_to_view: bpy.props.BoolProperty(name="Align to View", default=True)
    size: bpy.props.FloatProperty(name="Size", default=2.0, min=0.01, max=100.0)

    def execute(self, context):
        tmp_path, found = get_clipboard_image_path()

        if not found or tmp_path is None:
            self.report({'WARNING'},
                "No image found in clipboard. Try: right-click > Copy Image in Chrome/Edge, "
                "or copy a direct image URL (.png/.jpg/etc).")
            return {'CANCELLED'}

        try:
            import shutil
            dest_name = "blender_ref_" + str(int(time.time())) + ".png"
            dest_path = os.path.join(tempfile.gettempdir(), dest_name)
            shutil.copy2(tmp_path, dest_path)

            create_reference_image(context, dest_path, self.size, self.align_to_view)

            self.report({'INFO'}, "Reference image pasted.")
            return {'FINISHED'}

        except Exception as e:
            self.report({'ERROR'}, "Error: " + str(e))
            return {'CANCELLED'}

        finally:
            try:
                if tmp_path and os.path.exists(tmp_path):
                    os.unlink(tmp_path)
            except Exception:
                pass

    def invoke(self, context, event):
        return self.execute(context)


# ─────────────────────────────────────────────
#  N-Panel
# ─────────────────────────────────────────────

class VIEW3D_PT_paste_reference_panel(bpy.types.Panel):
    bl_label = "Reference Image"
    bl_idname = "VIEW3D_PT_paste_reference_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Reference"

    def draw(self, context):
        layout = self.layout
        sc = context.scene

        layout.label(text="Paste from Clipboard", icon='IMAGE_DATA')
        op = layout.operator(
            "view3d.paste_reference_image",
            text="Paste Reference  (Ctrl+Shift+V)",
            icon='PASTEDOWN',
        )
        op.size = sc.ref_paste_size
        op.align_to_view = sc.ref_paste_align

        layout.separator()
        layout.label(text="Options:", icon='SETTINGS')
        col = layout.column(align=True)
        col.prop(sc, "ref_paste_size", text="Size")
        col.prop(sc, "ref_paste_align", text="Align to view")

        layout.separator()
        layout.label(text="Accepted sources:", icon='INFO')
        layout.label(text="  - Copy Image (Chrome/Edge)")
        layout.label(text="  - Direct image URL (.png/.jpg/...)")
        layout.label(text="  - HTML with img src")

        if sys.platform == "linux":
            layout.separator()
            layout.label(text="Linux: requires xclip or wl-paste", icon='ERROR')


# ─────────────────────────────────────────────
#  Keymap
# ─────────────────────────────────────────────

addon_keymaps = []

def register_keymap():
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name='3D View', space_type='VIEW_3D')
        kmi = km.keymap_items.new(
            'view3d.paste_reference_image',
            type='V', value='PRESS', ctrl=True, shift=True,
        )
        addon_keymaps.append((km, kmi))

def unregister_keymap():
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()


# ─────────────────────────────────────────────
#  Register
# ─────────────────────────────────────────────

classes = (
    VIEW3D_OT_paste_reference_image,
    VIEW3D_PT_paste_reference_panel,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.ref_paste_size = bpy.props.FloatProperty(
        name="Size", default=2.0, min=0.01, max=100.0)
    bpy.types.Scene.ref_paste_align = bpy.props.BoolProperty(
        name="Align to view", default=True)
    register_keymap()

def unregister():
    unregister_keymap()
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.ref_paste_size
    del bpy.types.Scene.ref_paste_align

if __name__ == "__main__":
    register()
