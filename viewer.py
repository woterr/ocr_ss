import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gdk, Gio, cairo


class Overlay(Gtk.DrawingArea):
    def __init__(self, boxes, img_w, img_h):
        super().__init__()
        self.boxes = boxes
        self.img_w = img_w
        self.img_h = img_h

        # runtime state
        self.scale = 1.0
        self.offset_x = 0
        self.offset_y = 0

        # mouse click controller
        click = Gtk.GestureClick()
        click.connect("pressed", self.on_click)
        self.add_controller(click)

        # keyboard controller
        motion = Gtk.EventControllerMotion()
        motion.connect("motion", self.on_motion)
        self.add_controller(motion)
        
        self.set_draw_func(self.on_draw)

        self.set_focusable(True)
        self.set_can_focus(True)

        self.dragging = False
        self.drag_start = None
        self.drag_end = None



    # ---------------- drawing ----------------

    def on_draw(self, area, ctx, width, height):
        # compute render transform
        self.scale = min(width / self.img_w, height / self.img_h)

        render_w = self.img_w * self.scale
        render_h = self.img_h * self.scale

        self.offset_x = (width - render_w) / 2
        self.offset_y = (height - render_h) / 2

        for b in self.boxes:
            x = self.offset_x + b["x"] * self.scale
            y = self.offset_y + b["y"] * self.scale
            w = b["w"] * self.scale
            h = b["h"] * self.scale

            if b.get("selected"):
                ctx.set_source_rgba(1.0, 0.75, 0.2, 0.55)
            else:
                ctx.set_source_rgba(0.2, 0.5, 1.0, 0.25)

            ctx.rectangle(x, y, w, h)
            ctx.fill()

    # ---------------- interaction ----------------

def on_click(self, gesture, n_press, x, y):
    state = gesture.get_current_event_state()
    shift = state & Gdk.ModifierType.SHIFT_MASK

    hit_any = False

    for b in self.boxes:
        bx = self.offset_x + b["x"] * self.scale
        by = self.offset_y + b["y"] * self.scale
        bw = b["w"] * self.scale
        bh = b["h"] * self.scale

        hit = bx <= x <= bx + bw and by <= y <= by + bh

        if hit:
            hit_any = True
            if shift:
                # toggle selection
                b["selected"] = not b.get("selected", False)
            else:
                b["selected"] = True
        else:
            if not shift:
                b["selected"] = False

    if hit_any:
        self.queue_draw()


    def on_key(self, controller, keyval, keycode, state):
        if (
            state & Gdk.ModifierType.CONTROL_MASK
            and keyval == Gdk.KEY_c
        ):
            selected = [b["text"] for b in self.boxes if b.get("selected")]
            if not selected:
                return False

            text = " ".join(selected)

            clipboard = self.get_display().get_clipboard()
            clipboard.set(text)

            return True

        return False


class Viewer(Gtk.Application):
    def __init__(self, image_path, boxes):
        super().__init__(application_id="ocr.viewer")
        self.image_path = image_path
        self.boxes = boxes

    def do_activate(self):
        win = Gtk.ApplicationWindow(application=self)
        win.set_title("OCR Viewer")
        win.set_default_size(900, 600)

        file = Gio.File.new_for_path(self.image_path)
        texture = Gdk.Texture.new_from_file(file)

        img_w = texture.get_width()
        img_h = texture.get_height()

        image = Gtk.Picture.new_for_paintable(texture)
        image.set_content_fit(Gtk.ContentFit.CONTAIN)

        overlay = Gtk.Overlay()
        overlay.set_child(image)

        draw = Overlay(self.boxes, img_w, img_h)
        overlay.add_overlay(draw)

        draw.grab_focus()

        win.set_child(overlay)
        win.present()
