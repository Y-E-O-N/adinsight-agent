"""Phase 2C synthetic generation policy values.

이 파일은 generator 전반에서 공유하는 정책성 파라미터를 모은다.
Apify raw profile에서 계산되는 관측 분포는 별도 apify_profile.py / JSON으로 분리한다.
"""

from __future__ import annotations

SEED = 1125

REGIONS = ("KR", "JP")
REGION_PROBABILITIES = (0.7, 0.3)

CATEGORIES = ("beauty", "fashion", "food")
CATEGORY_PROBABILITIES = (0.5, 0.3, 0.2)

OBJECTIVES = ("conversion", "traffic", "awareness")
OBJECTIVE_PROBABILITIES = (0.6, 0.25, 0.15)

CAMPAIGN_DURATION_DAYS = (7, 14, 30)
CAMPAIGN_DURATION_PROBABILITIES = (0.4, 0.4, 0.2)
CAMPAIGN_BUDGET_MIN_KRW = 100_000

CREATOR_FOLLOWER_MIN = 200

CATEGORY_CONVERSION_MULTIPLIERS = {
    "beauty": 1.8,
    "fashion": 1.3,
    "food": 1.1,
}

REGION_CURRENCY = {
    "KR": ("KRW", 1.0),
    "JP": ("JPY", 9.5),
}

BASE_CVR = 0.015
ENGAGEMENT_CVR_WEIGHT = 3.0
SPONSORED_FATIGUE_WEIGHT = 1.5
MIN_CONVERSION_MULTIPLIER = 0.1

PAYMENT_TIER_BASE_RATES = {
    "low": 0.03,
    "medium": 0.12,
    "high": 0.45,
    "viral": 1.50,
}

PAYMENT_OBJECTIVE_MULTIPLIERS = {
    "conversion": 1.25,
    "traffic": 0.85,
    "awareness": 0.45,
}

PAYMENT_ENGAGEMENT_LOG_WEIGHT = 0.035
PAYMENT_BUDGET_REFERENCE_KRW = 1_000_000
PAYMENT_BUDGET_MULTIPLIER_MIN = 0.35
PAYMENT_BUDGET_MULTIPLIER_MAX = 3.00
PAYMENT_PAID_PARTNERSHIP_MULTIPLIER = 1.15
PAYMENT_AMOUNT_LOGNORMAL_MEAN = 9.2
PAYMENT_AMOUNT_LOGNORMAL_SIGMA = 0.7
PAYMENT_REFUND_PROBABILITY = 0.03

SOURCE_HASHTAG_CATEGORY_HINTS = {
    "뷰티": "beauty",
    "올리브영": "beauty",
    "다이소화장품": "beauty",
    "올영세일": "beauty",
    "올영": "beauty",
    "올영추천템": "beauty",
    "올영세일추천템": "beauty",
    "k뷰티": "beauty",
    "뷰티팁": "beauty",
    "뷰티꿀팁": "beauty",
    "기초화장품": "beauty",
    "메이크업": "beauty",
    "코덕": "beauty",
    "뷰티릴스": "beauty",
    "화장품추천": "beauty",
    "제품리뷰": "beauty",
    "솔직리뷰": "beauty",
    "ootd": "fashion",
    "꾸안꾸": "fashion",
    "요즘패션": "fashion",
    "grwm": "fashion",
}
