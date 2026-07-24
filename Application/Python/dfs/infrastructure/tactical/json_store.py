"""Versioned JSON persistence for independent Tactical Assistant game files."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from dfs.domain.tactical import (
    CriticalHitState,
    GamePhase,
    TacticalGameState,
    TacticalUnitState,
    TrackState,
    TraitState,
    UnitDisposition,
    UnitKind,
    WeaponState,
)


class TacticalGameFileError(ValueError):
    pass


def _track_payload(track: TrackState) -> dict[str, Any]:
    return {
        "maximum": track.maximum,
        "current": track.current,
        "threshold": track.threshold,
        "recovery": track.recovery,
    }


def _track_from_payload(
    payload: dict[str, Any] | None, *, allow_negative: bool = False
) -> TrackState:
    data = payload or {}
    maximum = data.get("maximum")
    current = data.get("current")
    threshold = data.get("threshold")
    track = TrackState(
        maximum=int(maximum) if maximum is not None else None,
        current=int(current) if current is not None else None,
        threshold=int(threshold) if threshold is not None else None,
        recovery=str(data.get("recovery", "")),
    )
    if track.maximum is None and track.current is not None:
        raise TacticalGameFileError("A tactical track cannot have a current value without a maximum.")
    if track.maximum is not None:
        current_valid = (
            track.current is not None
            and track.current <= track.maximum
            and (allow_negative or track.current >= 0)
        )
        if track.maximum < 0 or not current_valid:
            raise TacticalGameFileError("A tactical track contains an invalid current/maximum value.")
    return track


class JSONTacticalGameStore:
    FILE_EXTENSION = ".dfs-game.json"

    def save(self, game: TacticalGameState, path: str | Path) -> Path:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": game.schema_version,
            "game_id": game.game_id,
            "name": game.name,
            "game_system_id": game.game_system_id,
            "source_fleet_id": game.source_fleet_id,
            "source_fleet_name": game.source_fleet_name,
            "turn_number": game.turn_number,
            "phase": game.phase.value,
            "units": [self._unit_payload(unit) for unit in game.units],
            "notes": game.notes,
            "metadata": dict(game.metadata),
            "scenario_key": game.scenario_key,
            "scenario_priority": game.scenario_priority,
            "player_role": game.player_role,
            "scenario_objectives": dict(game.scenario_objectives),
            "victory_points": game.victory_points,
            "opponent_victory_points": game.opponent_victory_points,
            "battle_report_notes": game.battle_report_notes,
            "ended_at": game.ended_at,
            "created_at": game.created_at,
            "updated_at": game.updated_at,
        }
        temporary = target.with_suffix(target.suffix + ".tmp")
        temporary.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        temporary.replace(target)
        return target

    def load(self, path: str | Path) -> TacticalGameState:
        source = Path(path)
        try:
            payload: dict[str, Any] = json.loads(source.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise TacticalGameFileError(f"Unable to read tactical game file: {source}") from exc

        version = int(payload.get("schema_version", 0))
        if version != TacticalGameState.CURRENT_SCHEMA_VERSION:
            raise TacticalGameFileError(
                f"Unsupported tactical game schema version {version}; "
                f"expected {TacticalGameState.CURRENT_SCHEMA_VERSION}."
            )
        try:
            units = tuple(self._unit_from_payload(item) for item in payload.get("units", []))
            game = TacticalGameState(
                schema_version=version,
                game_id=str(payload["game_id"]),
                name=str(payload.get("name", "Untitled Game")),
                game_system_id=str(payload["game_system_id"]),
                source_fleet_id=str(payload["source_fleet_id"]),
                source_fleet_name=str(payload.get("source_fleet_name", "")),
                turn_number=int(payload.get("turn_number", 1)),
                phase=GamePhase(str(payload.get("phase", GamePhase.SETUP.value))),
                units=units,
                notes=str(payload.get("notes", "")),
                metadata=dict(payload.get("metadata", {})),
                scenario_key=str(payload.get("scenario_key", "")),
                scenario_priority=str(payload.get("scenario_priority", "")),
                player_role=str(payload.get("player_role", "")),
                scenario_objectives=dict(payload.get("scenario_objectives", {})),
                victory_points=max(0, int(payload.get("victory_points", 0))),
                opponent_victory_points=max(
                    0, int(payload.get("opponent_victory_points", 0))
                ),
                battle_report_notes=str(payload.get("battle_report_notes", "")),
                ended_at=str(payload.get("ended_at", "")),
                created_at=str(payload.get("created_at", "")),
                updated_at=str(payload.get("updated_at", "")),
            )
        except (KeyError, TypeError, ValueError) as exc:
            if isinstance(exc, TacticalGameFileError):
                raise
            raise TacticalGameFileError(f"Invalid tactical game file: {source}") from exc
        self._validate_game(game)
        return game

    @staticmethod
    def _unit_payload(unit: TacticalUnitState) -> dict[str, Any]:
        return {
            "unit_id": unit.unit_id,
            "source_entry_id": unit.source_entry_id,
            "profile_id": unit.profile_id,
            "parent_unit_id": unit.parent_unit_id,
            "kind": unit.kind.value,
            "platform_name": unit.platform_name,
            "vessel_name": unit.vessel_name,
            "instance_number": unit.instance_number,
            "faction_name": unit.faction_name,
            "fleet_name": unit.fleet_name,
            "priority_level": unit.priority_level,
            "initiative": unit.initiative,
            "speed": unit.speed,
            "turn": unit.turn,
            "hull": unit.hull,
            "troops": unit.troops,
            "source_notes": list(unit.source_notes),
            "metadata": dict(unit.metadata),
            "damage": _track_payload(unit.damage),
            "crew": _track_payload(unit.crew),
            "shields": _track_payload(unit.shields),
            "crew_quality": unit.crew_quality,
            "traits": [
                {
                    "trait_key": trait.trait_key,
                    "name": trait.name,
                    "disabled": trait.disabled,
                    "destroyed": trait.destroyed,
                }
                for trait in unit.traits
            ],
            "weapons": [
                {
                    "weapon_key": weapon.weapon_key,
                    "name": weapon.name,
                    "arc": weapon.arc,
                    "range_value": weapon.range_value,
                    "attack_dice": weapon.attack_dice,
                    "traits": weapon.traits,
                    "disabled": weapon.disabled,
                    "destroyed": weapon.destroyed,
                }
                for weapon in unit.weapons
            ],
            "critical_hits": [
                {
                    "critical_id": critical.critical_id,
                    "label": critical.label,
                    "effect": critical.effect,
                    "repaired": critical.repaired,
                    "notes": critical.notes,
                    "rule_key": critical.rule_key,
                    "system": critical.system,
                    "roll": critical.roll,
                    "damage_loss": critical.damage_loss,
                    "crew_loss": critical.crew_loss,
                    "speed_penalty": critical.speed_penalty,
                    "weapon_ad_penalty": critical.weapon_ad_penalty,
                    "no_special_actions": critical.no_special_actions,
                    "no_damage_control": critical.no_damage_control,
                    "no_damage_control_this_turn": critical.no_damage_control_this_turn,
                    "troop_penalty": critical.troop_penalty,
                    "power_fluctuations": critical.power_fluctuations,
                    "adrift": critical.adrift,
                    "target_kind": critical.target_kind,
                    "target_keys": list(critical.target_keys),
                    "target_labels": list(critical.target_labels),
                    "repairable": critical.repairable,
                    "applied_turn": critical.applied_turn,
                    "before_damage": critical.before_damage,
                    "before_crew": critical.before_crew,
                    "before_crippled": critical.before_crippled,
                    "before_skeleton_crew": critical.before_skeleton_crew,
                    "before_destroyed": critical.before_destroyed,
                    "before_special_action": critical.before_special_action,
                }
                for critical in unit.critical_hits
            ],
            "special_action": unit.special_action,
            "craft_status": unit.craft_status,
            "disposition": unit.disposition.value,
            "notes": unit.notes,
            "destroyed": unit.destroyed,
            "crippled": unit.crippled,
            "skeleton_crew": unit.skeleton_crew,
            "crippled_correction": unit.crippled_correction,
            "skeleton_crew_correction": unit.skeleton_crew_correction,
        }

    @staticmethod
    def _unit_from_payload(payload: dict[str, Any]) -> TacticalUnitState:
        damage = _track_from_payload(payload.get("damage"), allow_negative=True)
        crew = _track_from_payload(payload.get("crew"))
        inferred_crippled = bool(
            damage.threshold is not None
            and damage.current is not None
            and damage.current <= damage.threshold
        )
        inferred_skeleton = bool(
            crew.threshold is not None
            and crew.current is not None
            and crew.current <= crew.threshold
        )
        return TacticalUnitState(
            unit_id=str(payload["unit_id"]),
            source_entry_id=str(payload["source_entry_id"]),
            profile_id=(int(payload["profile_id"]) if payload.get("profile_id") is not None else None),
            parent_unit_id=(str(payload["parent_unit_id"]) if payload.get("parent_unit_id") else None),
            kind=UnitKind(str(payload["kind"])),
            platform_name=str(payload["platform_name"]),
            vessel_name=str(payload.get("vessel_name", "")),
            instance_number=int(payload.get("instance_number", 1)),
            faction_name=str(payload.get("faction_name", "")),
            fleet_name=str(payload.get("fleet_name", "")),
            priority_level=str(payload.get("priority_level", "")),
            initiative=str(payload.get("initiative", "")),
            speed=str(payload.get("speed", "")),
            turn=str(payload.get("turn", "")),
            hull=str(payload.get("hull", "")),
            troops=str(payload.get("troops", "")),
            source_notes=tuple(str(item) for item in payload.get("source_notes", [])),
            metadata=dict(payload.get("metadata", {})),
            damage=damage,
            crew=crew,
            shields=_track_from_payload(payload.get("shields")),
            crew_quality=str(payload.get("crew_quality", "")),
            traits=tuple(
                TraitState(
                    trait_key=str(item["trait_key"]),
                    name=str(item["name"]),
                    disabled=bool(item.get("disabled", False)),
                    destroyed=bool(item.get("destroyed", False)),
                )
                for item in payload.get("traits", [])
            ),
            weapons=tuple(
                WeaponState(
                    weapon_key=str(item["weapon_key"]),
                    name=str(item["name"]),
                    arc=str(item.get("arc", "")),
                    range_value=str(item.get("range_value", "")),
                    attack_dice=str(item.get("attack_dice", "")),
                    traits=str(item.get("traits", "")),
                    disabled=bool(item.get("disabled", False)),
                    destroyed=bool(item.get("destroyed", False)),
                )
                for item in payload.get("weapons", [])
            ),
            critical_hits=tuple(
                CriticalHitState(
                    critical_id=str(item["critical_id"]),
                    label=str(item["label"]),
                    effect=str(item.get("effect", "")),
                    repaired=bool(item.get("repaired", False)),
                    notes=str(item.get("notes", "")),
                    rule_key=str(item.get("rule_key", "")),
                    system=str(item.get("system", "")),
                    roll=str(item.get("roll", "")),
                    damage_loss=int(item.get("damage_loss", 0)),
                    crew_loss=int(item.get("crew_loss", 0)),
                    speed_penalty=int(item.get("speed_penalty", 0)),
                    weapon_ad_penalty=int(item.get("weapon_ad_penalty", 0)),
                    no_special_actions=bool(item.get("no_special_actions", False)),
                    no_damage_control=bool(item.get("no_damage_control", False)),
                    no_damage_control_this_turn=bool(
                        item.get("no_damage_control_this_turn", False)
                    ),
                    troop_penalty=int(item.get("troop_penalty", 0)),
                    power_fluctuations=bool(item.get("power_fluctuations", False)),
                    adrift=bool(item.get("adrift", False)),
                    target_kind=str(item.get("target_kind", "")),
                    target_keys=tuple(str(value) for value in item.get("target_keys", [])),
                    target_labels=tuple(str(value) for value in item.get("target_labels", [])),
                    repairable=bool(item.get("repairable", True)),
                    applied_turn=max(1, int(item.get("applied_turn", 1))),
                    before_damage=(
                        int(item["before_damage"])
                        if item.get("before_damage") is not None
                        else None
                    ),
                    before_crew=(
                        int(item["before_crew"])
                        if item.get("before_crew") is not None
                        else None
                    ),
                    before_crippled=bool(item.get("before_crippled", False)),
                    before_skeleton_crew=bool(item.get("before_skeleton_crew", False)),
                    before_destroyed=bool(item.get("before_destroyed", False)),
                    before_special_action=str(item.get("before_special_action", "")),
                )
                for item in payload.get("critical_hits", [])
            ),
            special_action=str(payload.get("special_action", "")),
            craft_status=str(payload.get("craft_status", "ready")),
            disposition=UnitDisposition(str(payload.get("disposition", "operational"))),
            notes=str(payload.get("notes", "")),
            destroyed=bool(payload.get("destroyed", False)),
            crippled=bool(payload.get("crippled", inferred_crippled)),
            skeleton_crew=bool(payload.get("skeleton_crew", inferred_skeleton)),
            crippled_correction=bool(payload.get("crippled_correction", False)),
            skeleton_crew_correction=bool(payload.get("skeleton_crew_correction", False)),
        )

    @staticmethod
    def _validate_game(game: TacticalGameState) -> None:
        if game.turn_number < 1:
            raise TacticalGameFileError("turn_number must be at least 1")
        unit_ids = [unit.unit_id for unit in game.units]
        if len(unit_ids) != len(set(unit_ids)):
            raise TacticalGameFileError("Duplicate tactical unit IDs are not allowed.")
        unit_id_set = set(unit_ids)
        for unit in game.units:
            if unit.parent_unit_id and unit.parent_unit_id not in unit_id_set:
                raise TacticalGameFileError(
                    f"Unit {unit.unit_id} references missing parent {unit.parent_unit_id}."
                )
            if unit.kind is UnitKind.CRAFT and unit.craft_status.casefold() not in {
                "ready",
                "launched",
            }:
                raise TacticalGameFileError(
                    f"Craft {unit.unit_id} has invalid status {unit.craft_status!r}."
                )
