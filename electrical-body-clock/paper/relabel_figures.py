"""Create publication-safe relabeled copies of legacy raster figures.

Only text-bearing regions are replaced. Plotted data, anatomy, colors, axes,
confidence intervals, and bar lengths remain unchanged.
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent / "figs_full"
FONT_SANS = Path(r"C:\Windows\Fonts\arial.ttf")
FONT_SANS_BOLD = Path(r"C:\Windows\Fonts\arialbd.ttf")
FONT_SERIF = Path(r"C:\Windows\Fonts\times.ttf")
FONT_SERIF_BOLD = Path(r"C:\Windows\Fonts\timesbd.ttf")


def font(path: Path, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(path), size=size)


def center_text(draw: ImageDraw.ImageDraw, box, text, fnt, fill="black", spacing=4):
    x0, y0, x1, y1 = box
    bbox = draw.multiline_textbbox((0, 0), text, font=fnt, spacing=spacing, align="center")
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.multiline_text(
        (x0 + (x1 - x0 - w) / 2, y0 + (y1 - y0 - h) / 2),
        text,
        font=fnt,
        fill=fill,
        spacing=spacing,
        align="center",
    )


def relabel_lemon():
    src = ROOT / "fig1_disagreement_headline_300.png"
    out = ROOT / "fig1_disagreement_headline_revised.png"
    im = Image.open(src).convert("RGB")
    d = ImageDraw.Draw(im)

    # Panel headers.
    d.rectangle((0, 0, 1185, 67), fill="white")
    d.rectangle((1185, 0, im.width, 67), fill="white")
    d.text((23, 16), "a", font=font(FONT_SERIF_BOLD, 34), fill="black")
    center_text(d, (120, 0, 1160, 67), "Four complementary T1-derived aging views", font(FONT_SERIF, 34))
    d.text((1190, 16), "b", font=font(FONT_SERIF_BOLD, 34), fill="black")
    center_text(d, (1280, 0, 2665, 67), "Cross-view dispersion differs by age group", font(FONT_SERIF, 34))

    # Right-panel y-axis label, retaining ticks and the axis line.
    d.rectangle((1525, 175, 1660, 1030), fill="white")
    label = Image.new("RGBA", (760, 70), (255, 255, 255, 0))
    ld = ImageDraw.Draw(label)
    center_text(ld, (0, 0, 760, 70), "Cross-view dispersion  S_T1", font(FONT_SERIF, 31))
    label = label.rotate(90, expand=True, resample=Image.Resampling.BICUBIC)
    im.paste(label, (1565, 240), label)
    im.save(out, dpi=(300, 300))


def relabel_gait():
    src = ROOT / "fig_neurovector_gait_result.png"
    out = ROOT / "fig_neurovector_gait_result_revised.png"
    im = Image.open(src).convert("RGB")
    d = ImageDraw.Draw(im)

    d.rectangle((0, 0, im.width, 148), fill="white")
    center_text(
        d,
        (400, 8, 2420, 125),
        "No detectable association between baseline brain-channel disagreement\n"
        "and subsequent four-metre walk-performance change",
        font(FONT_SANS, 39),
        spacing=5,
    )

    d.rectangle((0, 135, 760, 850), fill="white")
    d.line((770, 145, 770, 932), fill="black", width=3)
    d.line((760, 405, 770, 405), fill="black", width=3)
    d.line((760, 735, 770, 735), fill="black", width=3)
    center_text(
        d,
        (12, 250, 735, 410),
        "PRIMARY: longitudinal\nannualized 4-m walk performance ~ D",
        font(FONT_SANS, 24),
    )
    center_text(
        d,
        (12, 572, 735, 730),
        "Secondary: cross-sectional\nbaseline 4-m walk performance ~ D",
        font(FONT_SANS, 24),
    )
    d.rectangle((560, 982, 2250, 1070), fill="white")
    center_text(
        d,
        (580, 986, 2240, 1065),
        "Effect estimate for D  (association with walk performance)",
        font(FONT_SANS, 27),
    )
    im.save(out, dpi=(300, 300))


def relabel_ct():
    src = ROOT / "organ_age_ranking.png"
    out = ROOT / "organ_age_ranking_revised.png"
    im = Image.open(src).convert("RGB")
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, im.width, 190), fill="white")
    center_text(
        d,
        (0, 4, im.width, 62),
        "Anatomical localization in a volume-only CT age model  (n = 1,227)",
        font(FONT_SERIF, 38),
    )
    center_text(
        d,
        (250, 78, 1170, 154),
        "A. Structures contributing to held-out age estimation",
        font(FONT_SERIF, 31),
    )
    center_text(
        d,
        (1450, 78, 2440, 154),
        "B. Exploratory structure-gap differences by pathology label",
        font(FONT_SERIF, 30),
    )
    # Restore the top border of each plotting area.
    d.line((275, 190, 1188, 190), fill="black", width=2)
    d.line((1538, 190, 2448, 190), fill="black", width=2)
    im.save(out, dpi=(300, 300))


def relabel_skeleton():
    src = ROOT / "fig_skeleton_aging.png"
    out = ROOT / "fig_skeleton_aging_revised.png"
    im = Image.open(src).convert("RGB")
    d = ImageDraw.Draw(im)

    d.rectangle((0, 0, im.width, 86), fill="white")
    center_text(
        d,
        (0, 3, im.width, 82),
        "Cross-sectional bone-volume associations with age",
        font(FONT_SANS_BOLD, 45),
    )

    # Replace the legacy structure-specific callout with the canonical
    # group-level atlas values used in the revised Results and caption.
    d.rectangle((1070, 1190, 1418, 1468), fill="white")
    d.rounded_rectangle((1078, 1197, 1408, 1448), radius=12, fill=(248, 248, 248), outline=(190, 190, 190), width=2)
    callout = (
        "Largest group associations:\n"
        "femur       rho = 0.261\n"
        "pelvis      rho = 0.215\n"
        "lumbar      rho = 0.175\n"
        "sacrum      rho = 0.172\n"
        "thoracic    rho = 0.145"
    )
    d.multiline_text((1094, 1218), callout, font=font(FONT_SANS, 18), fill="black", spacing=5)

    d.rectangle((0, 1480, im.width, im.height), fill="white")
    center_text(
        d,
        (0, 1482, im.width, 1548),
        "Group-level cohort associations painted onto reference anatomy s1045",
        font(FONT_SANS, 25),
        fill=(65, 65, 65),
    )
    im.save(out, dpi=(300, 300))


if __name__ == "__main__":
    relabel_lemon()
    relabel_gait()
    relabel_ct()
    relabel_skeleton()
    for name in (
        "fig1_disagreement_headline_revised.png",
        "fig_neurovector_gait_result_revised.png",
        "organ_age_ranking_revised.png",
        "fig_skeleton_aging_revised.png",
    ):
        print(ROOT / name)
