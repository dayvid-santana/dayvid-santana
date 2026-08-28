# DSI GitHub Command Center
# Autor: Dayvid Santana
# Criado em: 28/08/2026
# Editado em: 28/08/2026
# Objetivo: Calcular a geometria de um radar de setores (fatias) para renderização em SVG.
"""Geometria pura para o gráfico radar de setores "Focus Sectors"."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass

DOT_COUNT = 10
DOT_CYCLE_SECONDS = 8.0


@dataclass(frozen=True)
class Sector:
    """Uma fatia do radar, já com o path SVG e a posição do rótulo calculados."""

    name: str
    count: int
    color: str
    path_d: str
    label_x: float
    label_y: float
    label_anchor: str
    count_label_y: float


@dataclass(frozen=True)
class SectorDot:
    """Uma partícula decorativa posicionada dentro do raio do radar."""

    x: float
    y: float
    color: str
    begin: float


@dataclass(frozen=True)
class SectorChart:
    """Radar de setores completo, pronto para ser iterado pelo template."""

    center_x: float
    center_y: float
    radius: float
    sectors: list[Sector]
    dots: list[SectorDot]
    sweep_tip_x: float
    sweep_tip_y: float


def build_sector_chart(
    counts: list[tuple[str, int]],
    colors: list[str],
    center_x: float = 637.0,
    center_y: float = 140.0,
    radius: float = 65.0,
    dot_count: int = DOT_COUNT,
    seed: int = 0,
) -> SectorChart | None:
    """Distribui `counts` em fatias proporcionais ao redor de um círculo, sem sobreposição."""
    total = sum(count for _, count in counts)
    if total <= 0:
        return None

    sectors: list[Sector] = []
    ranges: list[tuple[float, float, str]] = []
    angle = 0.0
    for index, (name, count) in enumerate(counts):
        color = colors[index % len(colors)]
        sweep = (count / total) * 360.0
        start_angle, end_angle = angle, angle + sweep
        ranges.append((start_angle, end_angle, color))

        start_x, start_y = _point(center_x, center_y, radius, start_angle)
        end_x, end_y = _point(center_x, center_y, radius, end_angle)
        large_arc = 1 if sweep > 180 else 0
        path_d = (
            f"M {center_x} {center_y} L {start_x:.1f} {start_y:.1f} "
            f"A {radius} {radius} 0 {large_arc} 1 {end_x:.1f} {end_y:.1f} Z"
        )

        label_x, label_y = _point(center_x, center_y, radius + 18, (start_angle + end_angle) / 2)
        sectors.append(
            Sector(
                name=name,
                count=count,
                color=color,
                path_d=path_d,
                label_x=round(label_x, 1),
                label_y=round(label_y, 1),
                label_anchor=_anchor_for(label_x, center_x),
                count_label_y=round(label_y + 12, 1),
            )
        )
        angle = end_angle

    rng = random.Random(seed)
    dots = [
        _random_dot(rng, center_x, center_y, radius, ranges, i, dot_count) for i in range(dot_count)
    ]

    tip_x, tip_y = _point(center_x, center_y, radius, 0.0)
    return SectorChart(
        center_x=center_x,
        center_y=center_y,
        radius=radius,
        sectors=sectors,
        dots=dots,
        sweep_tip_x=round(tip_x, 1),
        sweep_tip_y=round(tip_y, 1),
    )


def _random_dot(
    rng: random.Random,
    center_x: float,
    center_y: float,
    radius: float,
    ranges: list[tuple[float, float, str]],
    index: int,
    dot_count: int,
) -> SectorDot:
    dot_angle = rng.uniform(0.0, 360.0)
    dot_radius = rng.uniform(radius * 0.3, radius * 0.95)
    x, y = _point(center_x, center_y, dot_radius, dot_angle)
    color = next((color for start, end, color in ranges if start <= dot_angle <= end), ranges[0][2])
    begin = round((index / dot_count) * DOT_CYCLE_SECONDS, 2)
    return SectorDot(x=round(x, 1), y=round(y, 1), color=color, begin=begin)


def _point(
    center_x: float, center_y: float, radius: float, angle_degrees: float
) -> tuple[float, float]:
    """Converte um ângulo (0° = topo, sentido horário) em coordenadas cartesianas."""
    theta = math.radians(angle_degrees)
    return center_x + radius * math.sin(theta), center_y - radius * math.cos(theta)


def _anchor_for(label_x: float, center_x: float) -> str:
    if label_x > center_x + 3:
        return "start"
    if label_x < center_x - 3:
        return "end"
    return "middle"
