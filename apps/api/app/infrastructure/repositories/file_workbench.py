from __future__ import annotations

import json
from pathlib import Path
from typing import Generic, TypeVar

from pydantic import BaseModel

ModelT = TypeVar("ModelT", bound=BaseModel)


class JsonCollectionRepository(Generic[ModelT]):
    def __init__(self, workspace_root: str | Path, collection: str, model_type: type[ModelT], id_field: str) -> None:
        self.workspace_root = Path(workspace_root).resolve()
        self.model_type = model_type
        self.id_field = id_field
        self.path = self.workspace_root / ".working_dir" / "workbench" / f"{collection}.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def list(self) -> list[ModelT]:
        if not self.path.exists():
            return []
        payload = json.loads(self.path.read_text(encoding="utf-8") or "[]")
        return [self.model_type.model_validate(item) for item in payload]

    def get(self, item_id: str) -> ModelT:
        for item in self.list():
            if getattr(item, self.id_field) == item_id:
                return item
        raise KeyError(f"Unknown {self.model_type.__name__}: {item_id}")

    def upsert(self, item: ModelT) -> ModelT:
        items = self.list()
        item_id = getattr(item, self.id_field)
        replaced = False
        next_items = []
        for existing in items:
            if getattr(existing, self.id_field) == item_id:
                next_items.append(item)
                replaced = True
            else:
                next_items.append(existing)
        if not replaced:
            next_items.append(item)
        self._write(next_items)
        return item

    def delete(self, item_id: str) -> None:
        items = [item for item in self.list() if getattr(item, self.id_field) != item_id]
        self._write(items)

    def _write(self, items: list[ModelT]) -> None:
        self.path.write_text(json.dumps([item.model_dump() for item in items], ensure_ascii=False, indent=2), encoding="utf-8")
