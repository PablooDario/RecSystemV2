from .content_based import ContentBasedRecommender
from .personality import PersonalityMLPRecommender
from .popularity import PopularityRecommender

__all__ = [
    "ContentBasedRecommender",
    "PersonalityMLPRecommender",
    "PopularityRecommender",
]

try:
    from .lightgcn import LightGCN
    from .surprise_svd import SurpriseSVD, SurpriseSVDpp

    __all__ += [
        "SurpriseSVD",
        "SurpriseSVDpp",
        "LightGCN",
    ]
except ImportError:
    pass
