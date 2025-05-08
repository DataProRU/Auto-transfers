from collections.abc import Iterable, Sequence
from typing import Any

from django.db import models
from django.dispatch import Signal

vehicle_info_save = Signal()


class VehicleInfoManager(models.Manager):
    def bulk_create(  # noqa: PLR0913
        self,
        objs: Iterable[models.Model],
        batch_size: int | None = None,
        ignore_conflicts: bool = False,  # noqa: FBT001, FBT002
        update_conflicts: bool | None = None,
        update_fields: Sequence[str] | None = None,
        unique_fields: Sequence[str] | None = None,
    ) -> Any:  # noqa: ANN401
        created = super().bulk_create(
            objs, batch_size, ignore_conflicts, update_conflicts, update_fields, unique_fields
        )
        vehicle_info_save.send(sender=self.model, instances=created)
        return created
