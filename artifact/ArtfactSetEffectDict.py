from artifact.ArtifactSetEffect import *


ArtfactSetEffectDict = {
    cls().name: cls
    for name, cls in globals().items()
    if isinstance(cls, type) and isinstance(cls(), ArtifactEffect)
}
