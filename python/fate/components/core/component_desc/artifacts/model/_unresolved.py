from fate.components.core.essential import ModelUnresolvedArtifactType
from .._base_type import (
    URI,
    ArtifactDescribe,
    ModelOutputMetadata,
    Metadata,
    _ArtifactType,
    _ArtifactTypeReader,
    _ArtifactTypeWriter,
)


class ModelUnresolvedWriter(_ArtifactTypeWriter[ModelUnresolvedArtifactType]):
    def write_metadata(self, metadata: dict, name=None, namespace=None):
        self.artifact.metadata.metadata.update(metadata)
        if name is not None:
            self.artifact.metadata.name = name
        if namespace is not None:
            self.artifact.metadata.namespace = namespace


class ModelUnresolvedReader(_ArtifactTypeReader):
    def get_metadata(self):
        return self.artifact.metadata.metadata


class ModelUnresolvedArtifactDescribe(ArtifactDescribe[ModelUnresolvedArtifactType, ModelOutputMetadata]):
    @classmethod
    def get_type(cls):
        return ModelUnresolvedArtifactType

    def get_writer(self, config, ctx, uri: URI, type_name: str) -> ModelUnresolvedWriter:
        return ModelUnresolvedWriter(ctx, _ArtifactType(uri=uri, metadata=ModelOutputMetadata(), type_name=type_name))

    def get_reader(self, ctx, uri: "URI", metadata: "Metadata", type_name: str) -> ModelUnresolvedReader:
        return ModelUnresolvedReader(ctx, _ArtifactType(uri=uri, metadata=metadata, type_name=type_name))
