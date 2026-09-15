"""Business-data provider configuration."""

import os

from .base import BusinessDataProvider
from .http_provider import (
    DacquaBackendBusinessDataProvider,
)
from .providers import (
    UnavailableBusinessDataProvider,
)


BUSINESS_PROVIDER_ENV = (
    "DACQUA_BUSINESS_DATA_PROVIDER"
)

BACKEND_URL_ENV = (
    "DACQUA_BACKEND_BASE_URL"
)


def create_business_data_provider(
) -> BusinessDataProvider:
    """Create the configured business-data provider."""

    provider_name = os.environ.get(
        BUSINESS_PROVIDER_ENV,
        "unavailable",
    ).strip().lower()

    if provider_name == "unavailable":
        return (
            UnavailableBusinessDataProvider()
        )

    if provider_name == "dacqua_backend":
        base_url = os.environ.get(
            BACKEND_URL_ENV
        )

        if not base_url:
            raise RuntimeError(
                f"{BACKEND_URL_ENV} is required "
                f"when {BUSINESS_PROVIDER_ENV}"
                "=dacqua_backend."
            )

        return (
            DacquaBackendBusinessDataProvider(
                base_url
            )
        )

    raise RuntimeError(
        "Unsupported business-data provider: "
        f"{provider_name}"
    )
