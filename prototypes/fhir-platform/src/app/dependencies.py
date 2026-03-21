from typing import Annotated

from fastapi import Depends

from app.config import Settings, settings
from app.ingestion.fhir_client import FHIRClient
from app.projection.search_projector import SearchProjector


def get_settings() -> Settings:
    return settings


def get_fhir_client(cfg: Annotated[Settings, Depends(get_settings)]) -> FHIRClient:
    return FHIRClient(base_url=cfg.fhir_base_url)


def get_search_projector(cfg: Annotated[Settings, Depends(get_settings)]) -> SearchProjector:
    return SearchProjector()


SettingsDep = Annotated[Settings, Depends(get_settings)]
FHIRClientDep = Annotated[FHIRClient, Depends(get_fhir_client)]
SearchProjectorDep = Annotated[SearchProjector, Depends(get_search_projector)]
