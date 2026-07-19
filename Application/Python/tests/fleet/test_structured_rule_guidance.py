from dfs.domain.fleet.models import ValidationSeverity
from dfs.domain.fleet.rules import RuleMessage, RuleSource


def test_structured_remedies_are_preserved():
    message = RuleMessage(
        "TEST-001", ValidationSeverity.ERROR, "Test Rule", "Explanation",
        RuleSource("Book", "Section", 7),
        remedies=("Add one supporting ship.", "Remove the dependent choice."),
    )
    assert message.remedy_items == (
        "Add one supporting ship.",
        "Remove the dependent choice.",
    )


def test_legacy_remedy_remains_compatible():
    message = RuleMessage(
        "TEST-002", ValidationSeverity.ERROR, "Test Rule", "Explanation",
        RuleSource("Book"), remedy="Remove one choice; or increase the allowance.",
    )
    assert message.remedy_items == (
        "Remove one choice.",
        "Increase the allowance.",
    )
