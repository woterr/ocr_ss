import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gdk, Gio, GLib, Pango


# ---------- CSS ----------
def apply_ocr_css(widget):
    css = b"""
    label {
        color: transparent;
        background-color: transparent;
        padding: 0;
        margin: 0;
    }

    label selection {
        background-color: rgba(80, 140, 255, 0.45);
        color: transparent;
    }

    label:hover {
        background-color: rgba(255, 255, 255, 0.08);
    }
    """
    provider = Gtk.CssProvider()
    provider.load_from_data(css)
    widget.get_style_context().add_provider(
        provider,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )


# ---------- OCR Overlay ----------
class OCRTextLayer(Gtk.Fixed):
    def __init__(self, boxes, img_w, img_h):
        super().__init__()
        self.boxes = boxes
        self.img_w = img_w
        self.img_h = img_h

        self.labels = []
        self.scale = 1.0
        self.offset_x = 0
        self.offset_y = 0

        self.set_hexpand(True)
        self.set_vexpand(True)
        self.set_halign(Gtk.Align.FILL)
        self.set_valign(Gtk.Align.FILL)

    def rebuild(self, alloc_w, alloc_h):
        # clear old labels
        for lbl in self.labels:
            self.remove(lbl)
        self.labels.clear()

        if alloc_w <= 0 or alloc_h <= 0:
            return

        # match Gtk.Picture(CONTAIN) logic
        self.scale = min(alloc_w / self.img_w, alloc_h / self.img_h)
        render_w = self.img_w * self.scale
        render_h = self.img_h * self.scale

        self.offset_x = (alloc_w - render_w) / 2
        self.offset_y = (alloc_h - render_h) / 2

        for b in self.boxes:
            label = Gtk.Label(label=b["text"])
            label.set_selectable(True)
            label.set_xalign(0)
            label.set_yalign(0)
            label.set_wrap(False)

            # scale font to OCR height
            font_px = max(1, int(b["h"] * self.scale * 0.9))
            attrs = Pango.AttrList()
            attrs.insert(Pango.attr_size_new_absolute(font_px * Pango.SCALE))
            label.set_attributes(attrs)

            apply_ocr_css(label)

            x = self.offset_x + b["x"] * self.scale
            y = self.offset_y + b["y"] * self.scale

            # clip strictly inside rendered image
            if (
                x < self.offset_x or
                y < self.offset_y or
                x > self.offset_x + render_w or
                y > self.offset_y + render_h
            ):
                continue

            self.put(label, int(x), int(y))
            self.labels.append(label)


# ---------- Main Viewer ----------
class Viewer(Gtk.Application):
    def __init__(self, image_path, boxes):
        super().__init__(application_id="ocr.viewer")
        self.image_path = image_path
        self.boxes = boxes

    def do_activate(self):
        win = Gtk.ApplicationWindow(application=self)
        win.set_title("Screenshot")
        win.set_default_size(900, 600)

        # ----- Header bar -----
        header = Gtk.HeaderBar()
        win.set_titlebar(header)

        ocr_toggle = Gtk.ToggleButton(label="OCR")
        ocr_toggle.set_active(False)
        header.pack_end(ocr_toggle)

        # ----- Load image -----
        file = Gio.File.new_for_path(self.image_path)
        texture = Gdk.Texture.new_from_file(file)

        img_w = texture.get_width()
        img_h = texture.get_height()

        picture = Gtk.Picture.new_for_paintable(texture)
        picture.set_content_fit(Gtk.ContentFit.CONTAIN)
        picture.set_hexpand(True)
        picture.set_vexpand(True)

        # ----- Overlay -----
        overlay = Gtk.Overlay()
        overlay.set_child(picture)

        ocr_layer = OCRTextLayer(self.boxes, img_w, img_h)
        ocr_layer.set_visible(False)
        overlay.add_overlay(ocr_layer)

        # ----- Resize tracking (PICTURE-BASED) -----
        def on_picture_allocate(widget, allocation):
            if ocr_layer.get_visible():
                ocr_layer.rebuild(allocation.width, allocation.height)

        def rebuild_from_picture(*_):
            if not ocr_layer.get_visible():
                return
            w = picture.get_allocated_width()
            h = picture.get_allocated_height()
            if w > 0 and h > 0:
                ocr_layer.rebuild(w, h)

        picture.connect("notify::allocated-width", rebuild_from_picture)
        picture.connect("notify::allocated-height", rebuild_from_picture)

        # ----- Toggle behavior -----
        def toggle_ocr(btn):
            enabled = btn.get_active()
            ocr_layer.set_visible(enabled)

            if enabled:
                def deferred():
                    alloc = picture.get_allocation()
                    ocr_layer.rebuild(alloc.width, alloc.height)
                    return False
                GLib.idle_add(deferred)

        ocr_toggle.connect("toggled", toggle_ocr)

        win.set_child(overlay)
        win.present()
