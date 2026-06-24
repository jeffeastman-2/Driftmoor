"""Single import surface for the LATN parser.

The parser currently lives in the embedded Engraf package; phase 3 of the
integration will lift its core into a standalone ``latn`` package. Every
Driftmoor module that touches the parser imports from HERE, so that move is a
one-file change — repoint these imports and nothing else in Driftmoor changes.

(Engraf is an editable dependency: ``pip install -e ../Engraf`` into the
Driftmoor venv. The LATN core is numpy-only; the CAD/visualizer and Layer-6
extras are not imported here.)
"""

from latn.lexer.latn_layer_executor import LATNLayerExecutor
from latn.lexer.scene_adapter import SceneAdapter, GroundedEntity
from latn.lexer.lexicon import (
    Lexicon,
    get_active_lexicon,
    set_active_lexicon,
    use_lexicon,
)
from latn.lexer.vp_policy import (
    VPGroundingPolicy,
    PermissiveVPPolicy,
    set_active_vp_policy,
    use_vp_policy,
)
from latn.lexer.sp_policy import (
    SPGroundingPolicy,
    PermissiveSPPolicy,
    set_active_sp_policy,
    use_sp_policy,
)
from latn.lexer.spatial_policy import (
    SpatialPolicy,
    StrictSpatialPolicy,
    set_active_spatial_policy,
    use_spatial_policy,
)
from latn.lexer.vector_space import VectorSpace, vector_from_features
from latn.An_N_Space_Model.vocabulary import FUNCTION_WORDS
from latn.An_N_Space_Model.vector_dimensions import register_dimensions

__all__ = [
    "LATNLayerExecutor",
    "SceneAdapter",
    "GroundedEntity",
    "Lexicon",
    "get_active_lexicon",
    "set_active_lexicon",
    "use_lexicon",
    "VPGroundingPolicy",
    "PermissiveVPPolicy",
    "set_active_vp_policy",
    "use_vp_policy",
    "SPGroundingPolicy",
    "PermissiveSPPolicy",
    "set_active_sp_policy",
    "use_sp_policy",
    "SpatialPolicy",
    "StrictSpatialPolicy",
    "set_active_spatial_policy",
    "use_spatial_policy",
    "VectorSpace",
    "vector_from_features",
    "FUNCTION_WORDS",
    "register_dimensions",
]
