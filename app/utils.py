def risk_label(score: int) -> str:
    if score <= -20:
        return "SCAMMER"
    if score <= -10:
        return "HIGH_RISK"
    if score < 0:
        return "CAUTION"
    if score >= 20:
        return "TRUSTED"
    return "OK"
