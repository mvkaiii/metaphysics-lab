from .errors import ZiweiPhase2AError
from .models import LayerProvenance, Transformation, TransformationSet, TransformationType
from .transformation_profiles import PROFILE, PROFILE_ID, RULE_VERSION, validate_transformation_profile


def get_transformation_set(heavenly_stem, profile_id=PROFILE_ID):
    if profile_id != PROFILE_ID:
        raise ZiweiPhase2AError(
            "unknown_profile",
            "unknown Ziwei transformation profile",
            {"profile_id": profile_id},
        )
    validate_transformation_profile(PROFILE_ID, RULE_VERSION, PROFILE)
    if heavenly_stem not in PROFILE:
        raise ZiweiPhase2AError(
            "invalid_heavenly_stem",
            "invalid heavenly stem",
            {"heavenly_stem": heavenly_stem},
        )
    types = tuple(TransformationType)
    transformations = tuple(
        Transformation(types[idx], star, idx)
        for idx, star in enumerate(PROFILE[heavenly_stem])
    )
    provenance = LayerProvenance(
        "project_derived",
        "Metaphysics Lab",
        None,
        PROFILE_ID,
        RULE_VERSION,
        "engine.ziwei.transformations",
    )
    return TransformationSet(
        heavenly_stem,
        PROFILE_ID,
        RULE_VERSION,
        transformations,
        provenance,
    )
