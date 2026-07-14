"""Replace em dashes embedded in vector figure labels with colons.

The script preserves the original figure PDFs and writes deterministic
``*_no_emdash.pdf`` variants used by the manuscript.
"""

from __future__ import annotations

import re
from pathlib import Path

import fitz


ROOT = Path(__file__).resolve().parent / "figs_full"
EM_DASH = chr(0x2014)

FIGURES = (
    "fig_perturbation_compass.pdf",
    "fig_s3_phase_profiles.pdf",
    "fig_s4_motionvector.pdf",
)


def rgb_from_int(value: int) -> tuple[float, float, float]:
    return (
        ((value >> 16) & 255) / 255.0,
        ((value >> 8) & 255) / 255.0,
        (value & 255) / 255.0,
    )


def clean_text(text: str) -> str:
    return re.sub(rf"\s*{re.escape(EM_DASH)}\s*", ": ", text)


def rewrite_figure(source: Path) -> Path:
    destination = source.with_name(f"{source.stem}_no_emdash.pdf")
    document = fitz.open(source)
    replacements: list[tuple[fitz.Page, fitz.Rect, fitz.Point, str, float, int]] = []

    for page in document:
        for block in page.get_text("dict")["blocks"]:
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    text = span.get("text", "")
                    if EM_DASH not in text:
                        continue
                    rect = fitz.Rect(span["bbox"])
                    rect.x0 -= 0.8
                    rect.y0 -= 0.5
                    rect.x1 += 0.8
                    rect.y1 += 0.5
                    origin = fitz.Point(span["origin"])
                    replacements.append(
                        (page, rect, origin, clean_text(text), span["size"], span["color"])
                    )
                    page.add_redact_annot(rect, fill=(1, 1, 1))

    if not replacements:
        raise RuntimeError(f"No embedded em dash found in {source.name}")

    for page in document:
        page.apply_redactions()

    for page, _, origin, text, size, color in replacements:
        page.insert_text(
            origin,
            text,
            fontname="helv",
            fontsize=size,
            color=rgb_from_int(color),
            overlay=True,
        )

    document.save(destination, garbage=4, deflate=True)
    document.close()

    check = fitz.open(destination)
    extracted = "".join(page.get_text() for page in check)
    check.close()
    if EM_DASH in extracted:
        raise RuntimeError(f"Em dash remains in {destination.name}")
    return destination


if __name__ == "__main__":
    for filename in FIGURES:
        print(rewrite_figure(ROOT / filename))
