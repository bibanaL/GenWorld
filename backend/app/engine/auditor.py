from app.schemas.patch import PatchOperation, PermissionLevel


class PatchAuditError(ValueError):
    pass


FORBIDDEN_PATHS = {
    "/schema_version",
    "/premise",
    "/seed",
}

ALLOWED_ROOTS = {
    "/time",
    "/player",
    "/entities",
    "/locations",
    "/factions",
    "/clocks",
    "/facts",
    "/event_queue",
}

HIGH_RISK_OPS = {"remove"}


def audit_patch_operations(
    operations: list[PatchOperation],
    permission_level: PermissionLevel,
) -> None:
    if not operations:
        raise PatchAuditError("Patch batch must include at least one operation.")

    if len(operations) > 50:
        raise PatchAuditError("Patch batch cannot include more than 50 operations.")

    for operation in operations:
        _audit_path(operation.path)
        _audit_operation(operation, permission_level)


def _audit_path(path: str) -> None:
    if path == "":
        raise PatchAuditError("Root path cannot be patched.")

    if not path.startswith("/"):
        raise PatchAuditError(f"Patch path must be a JSON Pointer: {path}")

    if path in FORBIDDEN_PATHS:
        raise PatchAuditError(f"Path is protected and cannot be patched: {path}")

    if any(path == protected or path.startswith(f"{protected}/") for protected in FORBIDDEN_PATHS):
        raise PatchAuditError(f"Path is protected and cannot be patched: {path}")

    if not any(path == root or path.startswith(f"{root}/") for root in ALLOWED_ROOTS):
        raise PatchAuditError(f"Path is outside allowed world-state roots: {path}")


def _audit_operation(operation: PatchOperation, permission_level: PermissionLevel) -> None:
    if operation.op in HIGH_RISK_OPS and permission_level not in {"high", "system"}:
        raise PatchAuditError(f"Operation requires high permission: {operation.op}")

    if operation.op in {"increase", "decrease"} and not _is_number(operation.value):
        raise PatchAuditError(f"Operation requires a numeric value: {operation.op}")

    if operation.op == "add_status":
        if not isinstance(operation.value, dict):
            raise PatchAuditError("add_status requires an object value.")
        if not isinstance(operation.value.get("id"), str) or not operation.value["id"]:
            raise PatchAuditError("add_status value must include a non-empty string id.")

    if operation.op == "remove_status":
        if not isinstance(operation.value, str) or not operation.value:
            raise PatchAuditError("remove_status requires a non-empty status id string.")


def _is_number(value: object) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool)
