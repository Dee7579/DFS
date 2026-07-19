# Fleet Construction Rule Framework

Sprint 002D.1 adds reusable, source-backed construction-rule primitives. The
classes are game-data agnostic; published ACTA restrictions will be represented
as declarative instances during Sprint 002D.2.

## Available rule types

- `UniquePlatformRule`
- `MaximumQuantityRule`
- `RequiredPlatformRule`
- `MutualExclusionRule`
- `PurchaseRatioRule`
- `MinimumFleetRequirementRule`
- `FAPLimitedPlatformRule`
- `GroupedPurchaseRule`

`PlatformSelector` identifies affected profiles by stable profile IDs, fleet
list IDs, priorities, traits, or source books. Populated selector fields use AND
semantics. This avoids faction-specific conditionals in the Fleet Builder and
keeps future JSON rule catalogues possible.

Every rule returns a source citation, explanation, and remedy through the shared
`FleetRuleEngine`. Standard, Advisory, and Sandbox profiles can therefore apply
the same underlying rules with different enforcement policies.
