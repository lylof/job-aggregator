from abc import ABC, abstractmethod

class AbstractSource(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def get_listing_urls(self) -> list:
        pass

    @abstractmethod
    def get_listing_schema(self) -> dict:
        pass

    @abstractmethod
    def get_detail_schema(self) -> dict:
        pass

    @abstractmethod
    def get_item_unique_id(self, item_data: dict) -> str:
        pass

    def get_next_page_url(self, page_html: str, current_url: str) -> str | None:
        return None

    def normalize_date(self, raw_date: str) -> str | None:
        return None

    def normalize_experience(self, raw_exp: str) -> str | None:
        return None
