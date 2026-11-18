"""Completely simulated data — never present as Google GA4 measurements."""
from __future__ import annotations

import numpy as np
import pandas as pd


def make_demo(days: int = 56, sessions_per_day: int = 280, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    days_list = pd.date_range('2020-11-01', periods=days)
    rows = []
    counter = 0
    for ix, day in enumerate(days_list):
        n = int(rng.poisson(sessions_per_day))
        for _ in range(n):
            counter += 1
            device = str(rng.choice(['mobile', 'desktop', 'tablet'], p=[0.59, 0.36, 0.05]))
            country = str(rng.choice(['United States', 'Canada', 'United Kingdom'], p=[0.76, 0.15, 0.09]))
            source = str(rng.choice(['google', '(direct)', 'social', 'email'], p=[0.48, 0.30, 0.15, 0.07]))
            viewed = bool(rng.random() < (0.66 if source == 'social' else 0.73))
            cart = bool(viewed and rng.random() < (0.24 if device == 'mobile' else 0.31))
            checkout = bool(cart and rng.random() < 0.50)
            purchase_prob = 0.60 if device != 'mobile' else 0.46
            if ix >= days - 9 and device == 'mobile':
                purchase_prob = 0.21  # intentionally introduced DEMO scenario, not a true finding
            purchased = bool(checkout and rng.random() < purchase_prob)
            revenue = round(float(rng.uniform(25, 150)), 2) if purchased else 0.0
            rows.append((day.date().isoformat(), f'demo-{counter:07d}', device, country, source,
                         viewed, cart, checkout, purchased, revenue))
    return pd.DataFrame(rows, columns=['date','session_key','device','country','first_user_source',
                                       'viewed_item','added_to_cart','began_checkout','purchased','revenue'])
