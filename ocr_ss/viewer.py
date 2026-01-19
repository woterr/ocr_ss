import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gdk, Gio
import cairo

def load_css():
    css = b"""
    window {
        background-color: #0e0e0e;
    }

    button {
        background-color: rgba(255, 255, 255, 0.06);
        color: #eaeaea;
        border-radius: 10px;
        padding: 8px 14px;
        border: none;
        box-shadow: none;
    }

    button:hover {
        background-color: rgba(255, 255, 255, 0.12);
    }

    button:active {
        background-color: rgba(255, 255, 255, 0.18);
    }

    button.copy {
        background-color: rgba(255, 255, 255, 0.10);
        font-weight: 600;
    }

    button.copy:hover {
        background-color: rgba(255, 255, 255, 0.16);
    }
    """
    provider = Gtk.CssProvider()
    provider.load_from_data(css)
    Gtk.StyleContext.add_provider_for_display(
        Gdk.Display.get_default(),
        provider,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )


def normalize_boxes(boxes):
    cleaned = []
    for b in boxes:
        t = b["text"].strip()
        if len(t) < 2:
            continue
        if sum(c.isalnum() for c in t) < 2:
            continue
        cleaned.append(b)
    return cleaned


class OcrOverlay(Gtk.DrawingArea):
    def __init__(self, boxes, img_w, img_h):
        super().__init__()
        self.boxes = normalize_boxes(boxes)
        self.img_w = img_w
        self.img_h = img_h

        self.set_hexpand(True)
        self.set_vexpand(True)
        self.set_draw_func(self.on_draw)

    def on_draw(self, area, ctx, width, height):
        scale = min(width / self.img_w, height / self.img_h)
        rw = self.img_w * scale
        rh = self.img_h * scale

        ox = (width - rw) / 2
        oy = (height - rh) / 2

        ctx.set_source_rgba(0, 0, 0, 0.42)
        ctx.paint()
        ctx.save()
        ctx.set_operator(cairo.OPERATOR_OVER)
        ctx.set_source_rgba(0, 0, 0, 0.25)

        for b in self.boxes:
            x = ox + b["x"] * scale
            y = oy + b["y"] * scale
            w = b["w"] * scale
            h = b["h"] * scale
            r = max(4, h * 0.25)

            self.round_rect(ctx, x - 6, y - 3, w + 12, h + 8, r)
            ctx.fill()

        ctx.restore()

        ctx.save()
        ctx.set_operator(cairo.OPERATOR_CLEAR)

        for b in self.boxes:
            x = ox + b["x"] * scale
            y = oy + b["y"] * scale
            w = b["w"] * scale
            h = b["h"] * scale
            r = max(4, h * 0.25)

            self.round_rect(ctx, x - 6, y - 3, w + 12, h + 8, r)
            ctx.fill()

        ctx.restore()
        ctx.set_source_rgba(1, 1, 1, 0.55)
        ctx.set_line_width(1.0)

        for b in self.boxes:
            x = ox + b["x"] * scale
            y = oy + b["y"] * scale
            w = b["w"] * scale
            h = b["h"] * scale
            r = max(4, h * 0.25)

            self.round_rect(ctx, x - 6, y - 3, w + 12, h + 8, r)
            ctx.stroke()

    def round_rect(self, ctx, x, y, w, h, r):
        ctx.new_sub_path()
        ctx.arc(x + w - r, y + r, r, -1.57, 0)
        ctx.arc(x + w - r, y + h - r, r, 0, 1.57)
        ctx.arc(x + r, y + h - r, r, 1.57, 3.14)
        ctx.arc(x + r, y + r, r, 3.14, 4.71)
        ctx.close_path()


class Viewer(Gtk.Application):
    def __init__(self, image_path, boxes):
        super().__init__(application_id="ocr.viewer")
        self.image_path = image_path
        self.boxes = normalize_boxes(boxes)

    def do_activate(self):

        load_css()
        win = Gtk.ApplicationWindow(application=self)
        win.set_title("Screenshot OCR")
        win.set_default_size(960, 700)

        ctrl = Gtk.EventControllerKey()
        ctrl.connect("key-pressed", self.on_key, win)
        win.add_controller(ctrl)

        texture = Gdk.Texture.new_from_file(Gio.File.new_for_path(self.image_path))
        img_w, img_h = texture.get_width(), texture.get_height()

        picture = Gtk.Picture.new_for_paintable(texture)
        picture.set_content_fit(Gtk.ContentFit.CONTAIN)
        picture.set_hexpand(True)
        picture.set_vexpand(True)

        overlay = Gtk.Overlay()
        overlay.set_child(picture)
        overlay.add_overlay(OcrOverlay(self.boxes, img_w, img_h))

        btn_copy = Gtk.Button(label="Copy All Text")
        btn_copy.add_css_class("copy")
        btn_copy.connect("clicked", lambda *_: self.copy_all())

        btn_close = Gtk.Button(label="Close")
        btn_close.connect("clicked", lambda *_: win.close())

        controls = Gtk.Box(spacing=12)
        controls.set_margin_top(10)
        controls.set_margin_bottom(10)
        controls.set_margin_start(10)
        controls.set_margin_end(10)
        controls.append(btn_copy)
        controls.append(btn_close)

        layout = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        layout.append(overlay)
        layout.append(controls)

        win.set_child(layout)
        win.present()

    def copy_all(self):
        text = " ".join(b["text"] for b in self.boxes)
        clipboard = Gdk.Display.get_default().get_clipboard()
        clipboard.set(text)

    def on_key(self, controller, keyval, keycode, state, win):
        if keyval == Gdk.KEY_Escape:
            win.close()
        if state & Gdk.ModifierType.CONTROL_MASK and keyval == Gdk.KEY_c:
            self.copy_all()
