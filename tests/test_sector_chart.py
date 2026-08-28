# DSI GitHub Command Center
# Autor: Dayvid Santana
# Criado em: 28/08/2026
# Editado em: 28/08/2026
# Objetivo: Validar a geometria pura do radar de setores "Focus Sectors".
"""Testes do cálculo de setores do gráfico radar."""

from dsi_profile.services.sector_chart import build_sector_chart


def test_sectors_cover_full_circle_proportionally() -> None:
    """Cada fatia deve varrer um ângulo proporcional à sua contagem, somando 360°."""
    chart = build_sector_chart(
        [("Backend", 2), ("Frontend", 1), ("Infra", 1)],
        colors=["#111111", "#222222", "#333333"],
    )
    assert chart is not None
    assert [sector.name for sector in chart.sectors] == ["Backend", "Frontend", "Infra"]
    assert [sector.count for sector in chart.sectors] == [2, 1, 1]
    assert chart.sectors[0].color == "#111111"
    assert chart.sectors[1].color == "#222222"


def test_colors_cycle_when_more_sectors_than_colors() -> None:
    """Com mais setores que cores, a paleta deve ciclar em vez de estourar o índice."""
    chart = build_sector_chart(
        [("A", 1), ("B", 1), ("C", 1)],
        colors=["#aaa", "#bbb"],
    )
    assert chart is not None
    assert [sector.color for sector in chart.sectors] == ["#aaa", "#bbb", "#aaa"]


def test_returns_none_when_total_is_zero() -> None:
    """Sem nenhuma contagem, não há geometria para desenhar."""
    assert build_sector_chart([], colors=["#fff"]) is None


def test_dots_are_deterministic_for_a_fixed_seed() -> None:
    """A mesma entrada e semente devem produzir sempre as mesmas partículas decorativas."""
    counts = [("Backend", 3), ("Frontend", 1)]
    colors = ["#111111", "#222222"]
    first = build_sector_chart(counts, colors, seed=7)
    second = build_sector_chart(counts, colors, seed=7)
    assert first is not None and second is not None
    assert first.dots == second.dots


def test_dots_stay_within_radius_of_center() -> None:
    """Toda partícula decorativa deve cair dentro do raio do radar."""
    chart = build_sector_chart([("Backend", 1)], colors=["#111111"], radius=65.0)
    assert chart is not None
    for dot in chart.dots:
        distance = ((dot.x - chart.center_x) ** 2 + (dot.y - chart.center_y) ** 2) ** 0.5
        assert distance <= chart.radius + 0.01
