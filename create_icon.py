#!/usr/bin/env python
"""
Icon Generator for Nabbr
Creates the application icon using PIL/Pillow.

Design: Clean geometric raccoon face. Big round head, rounded ears,
bold mask band, large teal eyes, light snout. No unnecessary detail.
Duolingo-level simplicity — reads perfectly at 16px.
"""

import math
import os
import shutil
import sys
from PIL import Image, ImageDraw, ImageFilter


def lerp(c1, c2, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))


def rmask(w, h, r):
    m = Image.new('L', (w, h), 0)
    ImageDraw.Draw(m).rounded_rectangle([(0, 0), (w-1, h-1)], r, fill=255)
    return m


def create_app_icon():
    print("Creating Nabbr icon...")

    S = 4
    C = 256 * S  # 1024

    # ─── Palette ──────────────────────────────────────────
    BG1        = (18, 18, 30, 255)
    BG2        = (25, 20, 42, 255)
    FUR        = (160, 160, 175, 255)   # Main face
    FUR_LIGHT  = (210, 210, 218, 255)   # Light areas
    FUR_WHITE  = (238, 238, 242, 255)   # Snout bright
    MASK       = (40, 40, 55, 255)      # Dark mask
    EAR_OUT    = (100, 100, 115, 255)   # Outer ear
    EAR_IN     = (145, 130, 145, 255)   # Inner ear
    TEAL       = (0, 215, 190, 255)     # Brand eyes
    PUPIL      = (12, 12, 20, 255)
    WHITE      = (255, 255, 255, 255)
    NOSE       = (55, 50, 62, 255)
    MOUTH      = (130, 125, 140, 180)
    VIOLET     = (120, 75, 255, 255)

    # ─── Background ───────────────────────────────────────
    bg = Image.new('RGBA', (C, C), (0, 0, 0, 0))
    pxl = bg.load()
    pad = int(C * 0.038)
    for y in range(pad, C - pad):
        t = (y - pad) / max(1, C - 2*pad - 1)
        c = lerp(BG1, BG2, t)
        for x in range(pad, C - pad):
            pxl[x, y] = c

    bg_mask = Image.new('L', (C, C), 0)
    bg_mask.paste(rmask(C-2*pad, C-2*pad, int(C*0.20)), (pad, pad))
    bg.putalpha(bg_mask)

    # Accent stripe at bottom
    stripe = Image.new('RGBA', (C, C), (0, 0, 0, 0))
    sh = int(C * 0.025)
    for y in range(C-pad-sh, C-pad):
        t = (y - (C-pad-sh)) / max(1, sh-1)
        ImageDraw.Draw(stripe).line(
            [(pad, y), (C-pad, y)],
            fill=lerp(VIOLET[:3]+(0,), TEAL[:3]+(22,), t))
    stripe.putalpha(Image.composite(
        stripe.split()[3], Image.new('L', (C, C), 0), bg_mask))
    bg = Image.alpha_composite(bg, stripe)

    # ─── Face ─────────────────────────────────────────────
    fl = Image.new('RGBA', (C, C), (0, 0, 0, 0))
    d = ImageDraw.Draw(fl)

    cx = C // 2
    cy = int(C * 0.54)

    # ── EARS (round, behind head) ─────────────────────────
    ear_r = int(C * 0.088)
    ear_y = cy - int(C * 0.24)

    for side in (-1, 1):
        ear_x = cx + side * int(C * 0.155)
        # Outer
        d.ellipse([ear_x - ear_r, ear_y - int(ear_r*0.3),
                   ear_x + ear_r, ear_y + int(ear_r*1.5)],
                  fill=EAR_OUT)
        # Inner
        ir = int(ear_r * 0.52)
        iy = ear_y + int(ear_r * 0.25)
        d.ellipse([ear_x - ir, iy, ear_x + ir, iy + int(ir*1.5)],
                  fill=EAR_IN)

    # ── HEAD (single clean ellipse, wide and round) ───────
    head_rx = int(C * 0.29)
    head_ry = int(C * 0.25)
    d.ellipse([cx - head_rx, cy - head_ry, cx + head_rx, cy + head_ry],
              fill=FUR)

    # ── LIGHTER FOREHEAD PATCH ────────────────────────────
    fh_w = int(C * 0.08)
    fh_t = cy - head_ry + int(C * 0.03)
    fh_b = cy - int(C * 0.06)
    d.ellipse([cx - fh_w, fh_t, cx + fh_w, fh_b], fill=FUR_LIGHT)

    # ── MASK BAND ─────────────────────────────────────────
    mask_y = cy - int(C * 0.025)
    mask_hw = int(C * 0.265)
    mask_hh = int(C * 0.06)

    # Clean wide ellipse mask
    d.ellipse([cx - mask_hw, mask_y - mask_hh,
               cx + mask_hw, mask_y + mask_hh], fill=MASK)

    # V-bridge going up between eyes
    bw = int(C * 0.03)
    bt = mask_y - mask_hh - int(C * 0.04)
    d.polygon([
        (cx - bw, mask_y - int(mask_hh * 0.3)),
        (cx, bt),
        (cx + bw, mask_y - int(mask_hh * 0.3)),
    ], fill=MASK)

    # ── EYES ──────────────────────────────────────────────
    eye_y = mask_y
    eye_sp = int(C * 0.115)
    R_E = int(C * 0.055)     # eye total
    R_I = int(C * 0.046)     # iris
    R_P = int(C * 0.022)     # pupil
    R_S = int(C * 0.011)     # shine

    for side in (-1, 1):
        ex = cx + side * eye_sp

        # Eye bg
        d.ellipse([ex-R_E, eye_y-R_E, ex+R_E, eye_y+R_E],
                  fill=(50, 50, 65, 255))
        # Iris
        d.ellipse([ex-R_I, eye_y-R_I, ex+R_I, eye_y+R_I], fill=TEAL)
        # Pupil
        d.ellipse([ex-R_P, eye_y-R_P, ex+R_P, eye_y+R_P], fill=PUPIL)
        # Shine
        sx, sy = ex - int(R_P*0.5), eye_y - int(R_P*0.5)
        d.ellipse([sx-R_S, sy-R_S, sx+R_S, sy+R_S], fill=WHITE)
        # 2nd shine
        s2x, s2y = ex + int(R_P*0.35), eye_y + int(R_P*0.3)
        r2 = max(2, R_S//2)
        d.ellipse([s2x-r2, s2y-r2, s2x+r2, s2y+r2],
                  fill=(255, 255, 255, 130))

    # ── MUZZLE (lighter oval below mask) ──────────────────
    mz_y = mask_y + mask_hh + int(C * 0.045)
    mz_w = int(C * 0.13)
    mz_h = int(C * 0.08)
    d.ellipse([cx - mz_w, mz_y - mz_h, cx + mz_w, mz_y + mz_h],
              fill=FUR_WHITE)

    # Cheek accents
    for side in (-1, 1):
        ch_x = cx + side * int(C * 0.10)
        ch_y = mz_y - int(C * 0.01)
        ch_r = int(C * 0.05)
        d.ellipse([ch_x-ch_r, ch_y - int(ch_r*0.4),
                   ch_x+ch_r, ch_y + int(ch_r*0.6)],
                  fill=FUR_LIGHT)

    # ── NOSE ──────────────────────────────────────────────
    ny = mz_y - int(C * 0.02)
    nw, nh = int(C * 0.025), int(C * 0.016)
    d.rounded_rectangle([cx-nw, ny-nh, cx+nw, ny+nh],
                        radius=max(1, int(nh*0.5)), fill=NOSE)
    # Shine dot
    ns = max(2, int(C * 0.005))
    d.ellipse([cx-ns-2, ny-ns, cx+ns-2, ny+ns],
              fill=(78, 73, 88, 255))

    # ── MOUTH ─────────────────────────────────────────────
    mt = ny + nh + int(C * 0.003)
    ml = int(C * 0.014)
    d.line([(cx, mt), (cx, mt + ml)],
           fill=MOUTH, width=max(2, int(C * 0.004)))
    for side in (-1, 1):
        pts = [(cx, mt + ml)]
        for i in range(1, 10):
            t = i / 9
            pts.append((
                int(cx + side * int(C * 0.014) * t),
                int(mt + ml + int(C * 0.003 * math.sin(t * math.pi/2)))
            ))
        d.line(pts, fill=MOUTH, width=max(2, int(C * 0.003)))

    # ─── Composite & export ───────────────────────────────
    bg = Image.alpha_composite(bg, fl)
    icon = bg.resize((256, 256), Image.LANCZOS)

    png_path = 'app_icon.png'
    ico_path = 'app_icon.ico'
    icon.save(png_path)

    try:
        sizes = [(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)]
        imgs = [bg.resize(s, Image.LANCZOS) for s in sizes]
        imgs[0].save(ico_path, format='ICO',
                     sizes=[(i.width, i.height) for i in imgs],
                     append_images=imgs[1:])
        print(f"ICO: {os.path.abspath(ico_path)}")
    except Exception as e:
        print(f"ICO failed ({e})")

    # Generate .icns for macOS (requires iconutil, macOS only)
    if sys.platform == 'darwin':
        import tempfile
        icns_path = 'app_icon.icns'
        try:
            iconset = tempfile.mkdtemp(suffix='.iconset')
            for s in [16, 32, 64, 128, 256, 512]:
                bg.resize((s, s), Image.LANCZOS).save(
                    os.path.join(iconset, f'icon_{s}x{s}.png'))
                bg.resize((s*2, s*2), Image.LANCZOS).save(
                    os.path.join(iconset, f'icon_{s}x{s}@2x.png'))
            import subprocess
            subprocess.run(['iconutil', '-c', 'icns', iconset, '-o', icns_path],
                           check=True)
            shutil.rmtree(iconset)
            print(f"ICNS: {os.path.abspath(icns_path)}")
        except Exception as e:
            print(f"ICNS failed ({e})")
    else:
        print("Skipping .icns (not on macOS)")

    print(f"PNG: {os.path.abspath(png_path)}")
    print("Done.")


if __name__ == "__main__":
    try:
        create_app_icon()
    except ImportError:
        print("Pillow required: pip install Pillow")
