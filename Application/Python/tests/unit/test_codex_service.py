from dfs.services.codex_service import CodexService


def test_parameterized_trait_resolves():
    entry = CodexService().get("Anti-Fighter 4")
    assert entry is not None
    assert entry.title == "Anti-Fighter"


def test_weapon_trait_resolves():
    entry = CodexService().first_for_weapon("Heavy Laser Cannon", "Beam, Double Damage")
    assert entry is not None
    assert entry.title in {"Beam", "Double Damage"}
