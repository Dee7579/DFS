from __future__ import annotations

from dfs.services.codex_service import CodexEntry, CodexService


def test_all_for_weapon_returns_every_recognized_trait(monkeypatch) -> None:
    service = CodexService()
    entries = {
        "accurate": CodexEntry("Accurate", "Weapon Trait", "Accurate rule text.", "Rulebook"),
        "anti-fighter": CodexEntry("Anti-Fighter", "Weapon Trait", "Anti-Fighter rule text.", "Rulebook"),
        "precise": CodexEntry("Precise", "Weapon Trait", "Precise rule text.", "Rulebook"),
    }

    monkeypatch.setattr(
        service,
        "get",
        lambda name: entries.get(str(name).casefold()),
    )

    resolved = service.all_for_weapon(
        "Uni-Pulse Cannon",
        "Accurate, Anti-Fighter, Precise",
    )

    assert [entry.title for entry in resolved] == [
        "Accurate",
        "Anti-Fighter",
        "Precise",
    ]
    assert service.first_for_weapon("Uni-Pulse Cannon", "Accurate, Precise").title == "Accurate"
