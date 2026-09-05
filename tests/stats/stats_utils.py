"""Pomocnicze funkcje statystyczne do protokolu walidacji TIMDR
(docs/PROPOSAL.md, sekcja 7): test Manna-Whitneya + effect size r.
"""

from dataclasses import dataclass

import numpy as np
from scipy.stats import mannwhitneyu, norm


@dataclass
class MannWhitneyResult:
    u_statistic: float
    p_value: float
    z_approx: float
    effect_size_r: float
    n1: int
    n2: int


def mannwhitney_with_effect_size(x: list[float], y: list[float], alternative: str = "two-sided") -> MannWhitneyResult:
    """Test Manna-Whitneya U + przyblizone z (z aproksymacji normalnej U)
    i effect size r = z / sqrt(N), zgodnie z konwencja uzywana w
    protokole TIMDR.
    """
    x_arr, y_arr = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
    n1, n2 = len(x_arr), len(y_arr)
    result = mannwhitneyu(x_arr, y_arr, alternative=alternative)

    mean_u = n1 * n2 / 2.0
    std_u = np.sqrt(n1 * n2 * (n1 + n2 + 1) / 12.0)
    z = (result.statistic - mean_u) / std_u if std_u > 0 else 0.0
    r = z / np.sqrt(n1 + n2) if (n1 + n2) > 0 else 0.0

    return MannWhitneyResult(
        u_statistic=float(result.statistic),
        p_value=float(result.pvalue),
        z_approx=float(z),
        effect_size_r=float(r),
        n1=n1,
        n2=n2,
    )


def estimate_power_two_sample(effect_size_r: float, n1: int, n2: int, alpha: float = 0.05) -> float | None:
    """Przyblizona moc testu, jesli dostepny jest statsmodels. Zwraca
    None jesli statsmodels nie jest zainstalowany (opcjonalna zaleznosc).
    """
    try:
        from statsmodels.stats.power import NormalIndPower
    except ImportError:
        return None

    # Konwersja r -> Cohen's d (przyblizenie dla duzych prob): d = 2r / sqrt(1-r^2)
    r = min(max(effect_size_r, -0.999), 0.999)
    d = 2 * r / np.sqrt(1 - r**2)
    analysis = NormalIndPower()
    ratio = n2 / n1 if n1 > 0 else 1.0
    return float(analysis.power(effect_size=abs(d), nobs1=n1, alpha=alpha, ratio=ratio))
