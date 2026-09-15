"""Authoritative business-data tool contracts."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal


BusinessQueryKind = Literal["price", "availability"]

BusinessToolStatus = Literal[
    "success",
    "restricted",
    "not_found",
    "unavailable",
]


@dataclass(frozen=True, slots=True)
class BusinessToolResult:
    """Customer-safe result returned by an authoritative business tool."""

    kind: BusinessQueryKind
    status: BusinessToolStatus
    text: str
    source: str


class BusinessDataProvider(ABC):
    """Runtime source for authoritative business information."""

    @abstractmethod
    def lookup_price(
        self,
        product_query: str,
    ) -> BusinessToolResult:
        """Return a policy-compliant current pricing result."""
        raise NotImplementedError

    @abstractmethod
    def lookup_availability(
        self,
        product_query: str,
    ) -> BusinessToolResult:
        """Return current inventory/installation availability."""
        raise NotImplementedError
