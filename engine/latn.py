"""Single import surface for the LATN parser.

The parser currently lives in the embedded Engraf package; phase 3 of the
integration will lift its core into a standalone ``latn`` package. Every
Driftmoor module that touches the parser imports from HERE, so that move is a
one-file change — repoint these imports and nothing else in Driftmoor changes.

(Engraf is an editable dependency: ``pip install -e ../Engraf`` into the
Driftmoor venv. The LATN core is numpy-only; the CAD/visualizer and Layer-6
extras are not imported here.)
"""

from engraf.lexer.latn_layer_executor import LATNLayerExecutor
from engraf.lexer.scene_adapter import SceneAdapter, GroundedEntity
from engraf.lexer.lexicon import (
    Lexicon,
    get_active_lexicon,
    set_active_lexicon,
    use_lexicon,
)
from engraf.lexer.vp_policy import (
    VPGroundingPolicy,
    PermissiveVPPolicy,
    set_active_vp_policy,
    use_vp_policy,
)
from engraf.lexer.spatial_policy import (
    SpatialPolicy,
    EngrafSpatialPolicy,
    set_active_spatial_policy,
    use_spatial_policy,
)
from engraf.lexer.vector_space import VectorSpace, vector_from_features
from engraf.An_N_Space_Model.vocabulary import FUNCTION_WORDS
from engraf.An_N_Space_Model.vector_dimensions import register_dimensions

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
    "SpatialPolicy",
    "EngrafSpatialPolicy",
    "set_active_spatial_policy",
    "use_spatial_policy",
    "VectorSpace",
    "vector_from_features",
    "FUNCTION_WORDS",
    "register_dimensions",
]
