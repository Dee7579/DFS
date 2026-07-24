"""Complete player-facing scenario rules text for Tactical Assistant.

The text is transcribed from the project-authoritative Rulebook and Powers &
Principalities sources.  It intentionally contains the operational scenario
sections rather than the introductory fiction so the in-game help remains
useful at the table.
"""
from __future__ import annotations

from textwrap import dedent


def _rules(text: str) -> str:
    return dedent(text).strip()


SCENARIO_FULL_RULES: dict[str, str] = {
    "ambush": _rules("""
        Source: Rulebook pp. 50-51

        Fleets: The defender has 5 Fleet Allocation Points. The attacker has 3 Fleet Allocation Points.

        Pre-Battle Preparation: The defending fleet is placed in the central deployment area marked on the map, with all ships pointing towards one short table edge. The attacker picks one of the deployment areas that run alongside the long table edges. He may place stellar debris how he wishes in this deployment area – all other stellar debris is generated randomly. He then places his ships in this deployment area though he is permitted to keep all but one ship in hyperspace, so long as he has at least one ship in hyperspace with the Jump Engine or Advanced Jump Engine trait.

        Scenario Rules: The attacker automatically wins Initiative in the first turn. The defending player may only act normally with his ships if they first pass a Crew Quality check (target number 10). If a ship fails this check, it must move 6” (or up to its maximum Speed if less than 6) in a straight line.

        Game Length: Until the attacker has withdrawn or until one side has no ships on the table (stricken, destroyed and surrendered ships do not count as viable ships).

        Victory and Defeat: This scenario uses Victory Points in order to determine who wins. However, the defending player does not gain Victory Points for enemy ships that tactically withdraw.
    """),
    "annihilation": _rules("""
        Source: Rulebook p. 51

        Fleets: Players have random Fleet Allocation Points and choose their fleets freely.

        Pre-Battle Preparation: Roll for Initiative as normal – the losing fleet will be forced to set up first. The fleets are deployed anywhere in their own deployment zones as shown on the scenario map. Stellar debris is generated randomly.

        Scenario Rules: None.

        Game Length: Until the victory conditions have been met.

        Victory and Defeat: For the fleets involved in this battle, damage sustained by their own ships is of little importance so long as the enemy suffers more. This battle will continue until all the ships on one side have been destroyed. The winner is the fleet with at least one ship remaining on the table.
    """),
    "assassination": _rules("""
        Source: Rulebook pp. 52-53

        Fleets: Players have random Fleet Allocation Points and choose their fleets freely.

        Pre-Battle Preparation: The defender deploys his fleet first. The attacker must nominate one ship in the enemy fleet at the highest priority level possible and secretly record its name on a scrap piece of paper. This ship is his target, the one marked for assassination. The attacker may keep up to half of his fleet in hyperspace at the beginning of the game, so long as he has at least one ship in hyperspace with the Jump Engine or Advanced Jump Engine trait. Stellar debris is generated randomly.

        Scenario Rules: None.

        Game Length: 12 turns, or until one fleet withdraws or either side has no ships on the table (stricken, destroyed and surrendered ships do not count as viable ships).

        Victory and Defeat: This scenario uses Victory Points in order to determine who wins. However, the attacker will earn +10 bonus Victory Points if he destroys his target ship. If the target ship is still on the table at the end of the game and not Stricken, the defender receives +10 bonus Victory Points.
    """),
    "blockade": _rules("""
        Source: Rulebook p. 53

        Fleets: The attacker (the blockader) has 5 Fleet Allocation Points. The defender (the blockade-runner) has 2 Fleet Allocation Points.

        Pre-Battle Preparation: The blockading player deploys his fleet first. All ships must be pointing directly towards the opposite long table edge. The blockade-runner will move all his ships on from anywhere along this opposite table edge in the first turn. The blockade-runner may not use the Initiate Jump Point! Special Action as the blockader is successfully jamming his jump engines. Stellar debris is generated randomly.

        Scenario Rules: The blockade-runner has one ‘free’ turn at the beginning of the battle. In effect, he may move and attack with his ships normally but the blockading fleet may do nothing – its ships may not move, fire, take Special Actions or perform Damage Control (though any traits still work as normal). They must simply take any damage dealt during this turn. After this first turn, Initiative is rolled normally.

        Game Length: 12 turns, or until the victory conditions have been met.

        Victory and Defeat: This scenario uses Victory Points in order to determine who wins. The blockading player scores Victory Points normally. The blockade-running player only scores Victory Points for moving ships off the blockader’s long table edge. He gains the full Victory Point value of every ship moved off the table in this way, regardless of its condition, as if it had been destroyed. The blockader’s long table edge and the two short table edges are considered to belong to the blockader for the purposes of tactical withdrawal. The opposite long table edge is considered to belong to the blockade-runner.
    """),
    "call-to-arms": _rules("""
        Source: Rulebook p. 54

        Fleets: Players have random Fleet Allocation Points and choose their fleets freely.

        Pre-Battle Preparation: Roll for Initiative – the losing fleet will be forced to set up first. The fleets are deployed anywhere in their own deployment zones as shown on the scenario map. This clash takes place in deep space and so no stellar debris or planets are required unless both players agree to their use.

        Scenario Rules: None.

        Game Length: 12 turns, or until either side has no ships on the table (stricken, destroyed and surrendered ships do not count as viable ships).

        Victory and Defeat: This scenario uses Victory Points in order to determine who wins.
    """),
    "carrier-clash": _rules("""
        Source: Rulebook p. 55

        Fleets: Players have random Fleet Allocation Points. Both fleets must have one ship with at least two flights of auxiliary craft. All other ships in the fleet must be of an equal or lower Priority Level than the scenario.

        Pre-Battle Preparation: Roll for Initiative as normal – the losing fleet will be forced to set up first. The fleets are deployed anywhere in their own deployment zones as shown on the scenario map. Stellar debris is generated randomly.

        Scenario Rules: None.

        Game Length: 12 turns, or until either side has no ships on the table (stricken, destroyed and surrendered ships do not count as viable ships).

        Victory and Defeat: This scenario uses Victory Points in order to determine who wins. The short table edges are considered to belong to the player who has his deployment zone there for the purposes of tactical withdrawal. The long table edges are considered to be neutral.
    """),
    "convoy-duty": _rules("""
        Source: Rulebook p. 56

        Fleets: The defending player has 5 Fleet Allocation Points. The defending player also has two corporate freighters. These are the convoy ships he must protect. For every increase in Priority Level above Patrol, the number of corporate freighters increases by two. A Priority Level: War game would therefore have ten corporate freighters. The attacker has 3 Fleet Allocation Points.

        Pre-Battle Preparation: The defending fleet is placed in the deployment area marked on the map. The attacker does not start on the table. Instead, he will move his ships on from either long table edge during any turn he chooses. He is not required to move all his ships on from the same table edge, nor is he required to move them all on in the same turn. The attacker may also keep up to half of his fleet in hyperspace at the beginning of the game, so long as he has at least one ship in hyperspace with the Jump Engine or Advanced Jump Engine trait. Stellar debris is generated randomly.

        Scenario Rules: The convoy ships are always moved in the End Phase of each turn.

        Game Length: Until the end of the turn in which all convoy ships have either been destroyed or have left the table (stricken, destroyed and surrendered ships do not count as viable ships).

        Victory and Defeat: This scenario uses Victory Points in order to determine who wins. However, the attacker will gain +2 bonus Victory Points for every convoy ship he manages to completely destroy (but no other Victory Points are earned for destroying these ships). The defender gains +2 bonus Victory Points for every convoy ship he manages to exit from the exit edge marked on the map and earns the usual Victory Points for destroying attacking ships. For the purposes of tactical withdrawal, the short edges are considered to belong to the defender while the long table edges belong to the attacker.

        Civilian Fleet Points: If you are using Civilian Fleet Points (see the Fleet Book), then you will earn +2 bonus Victory Points per CFP.
    """),
    "flee-to-jump-gate": _rules("""
        Source: Rulebook p. 57

        Fleets: The attacking player has 5 Fleet Allocation Points and chooses his fleet freely. At least one of his ships must have the Jump Point or Advanced Jump Point trait. The defending player has 3 Fleet Allocation Points.

        Pre-Battle Preparation: A jump gate is placed on the table, as shown on the map. The defending fleet is deployed first, with all ships pointing towards the jump gate. The attacker then chooses up to two ships to be placed in his deployment zones at the far corners of the table behind the defending fleet. The rest of his fleet is kept in hyperspace; at least one of these ships must have the Jump Engine or Advanced Jump Engine trait. The defending player may not use the Initiate Jump Point! Special Action as the attacker is successfully jamming his jump engines. The jump gate is considered to belong to the attacker, as defined in the Advanced Rules chapter. Stellar debris is generated randomly.

        Scenario Rules: The attacker moves his main force onto the table from the Surprise Entry Point on Turn 2. He must have a ship that is capable of opening this jump point in hyperspace.

        Game Length: 12 turns, or until the victory conditions have been met.

        Victory and Defeat: This scenario uses Victory Points in order to determine who wins. The attacker gains Victory Points as normal. The defending player gains the full Victory Point value of every one of his ships that exit via the jump gate, regardless of its condition, as if it had been destroyed. The defender also earns the usual Victory Points for destroying attacking ships.
    """),
    "planetary-assault": _rules("""
        Source: Rulebook p. 58

        Fleets: The attacking player has 7 Fleet Allocation Points to choose a fleet with. The defending player has 5 Fleet Allocation Points and also gains extra defences, as described in the Planetary Assault rules.

        Pre-Battle Preparation: The defender sets up in his deployment zone first. The attacker moves on from his short table edge in the first turn. The attacker is permitted to keep all but one of his ships in hyperspace, so long as he has at least one ship in hyperspace with the Jump Engine or Advanced Jump Engine trait.

        Scenario Rules: All the Planetary Assault rules are used in this scenario.

        Game Length: 12 turns or until Victory Conditions are met.

        Victory and Defeat: This scenario focuses on the planet rather than the fleets themselves. Planets are exceptionally important strategic targets and it would be worth the death of an entire fleet in order to capture or retain hold of one. The game continues until either the defender has no Troops left on the planet or the attacker has no Troops left to deploy. If, at this point, the defender still holds the planet with Troops, he has won (but may be in for a long blockade if his fleet has been wiped out). If the attacker has Troops on the planet but the defender does not, he gains victory. If the defender has Troops on the planet but no Emplacements, the fight is a draw.
    """),
    "planetfall": _rules("""
        Source: Rulebook p. 59

        Fleets: Players have random Fleet Allocation Points and choose their fleets freely.

        Pre-Battle Preparation: Roll for Initiative as normal – the losing fleet will be forced to set up first. The fleets are deployed anywhere in their own deployment zones as shown on the scenario map. The planet is placed in the centre and stellar debris is generated randomly.

        Scenario Rules: The first fleet to land on the planet will count as the defender in terms of Troops fighting one another.

        Game Length: 12 turns.

        Victory and Defeat: This scenario uses Victory Points in order to determine who wins. The side that has more Troops on the planet at the end of the game gains +10 bonus Victory Points.
    """),
    "recon-run": _rules("""
        Source: Rulebook p. 60

        Fleets: The defender has 5 Fleet Allocation Points and chooses his fleet freely. The attacker has 3 Fleet Allocation Points.

        Pre-Battle Preparation: The defending fleet is placed in the deployment area marked on the map. The attacker will move his ships on from any one table edge he chooses in the first turn of the game. The attacker may also keep up to half of his ships in hyperspace at the beginning of the game, so long as he has at least one ship in hyperspace with the Jump Engine or Advanced Jump Engine trait. Stellar debris is generated randomly.

        Scenario Rules: The objective of this scenario is for the attacker to successfully scan as many enemy ships (excluding fighters) as possible. To do this, he must move a ship within 12” of an enemy ship and then roll 1d6, adding his Crew Quality score. On a 7 or more, he successfully scans the enemy. Each attacking ship can scan one defending ship per turn. However, they may not perform any Special Actions while doing so. Fighters may never scan ships.

        Game Length: 12 turns, or until the end of the turn in which every defending ship (excluding fighters) has been scanned.

        Victory and Defeat: This scenario uses Victory Points in order to determine who wins. However, the attacker gains half of an enemy ship’s destroyed Victory Point value, rounding up, whenever he successfully scans it (excluding fighters). Each enemy ship may only be scanned once.
    """),
    "rescue": _rules("""
        Source: Rulebook p. 61

        Fleets: Players have random Fleet Allocation Points and choose their fleets freely.

        Pre-Battle Preparation: Roll for Initiative as normal – the losing fleet will be forced to set up first. The fleets are deployed anywhere in their own deployment zones as shown on the scenario map. Stellar debris is generated randomly. The objective ship is motionless for the entire battle and cannot be boarded or fired upon.

        Scenario Rules: None.

        Game Length: 12 turns.

        Victory and Defeat: This scenario uses Victory Points in order to determine who wins. The side that has a ship within 6” of the objective ship will gain +10 bonus Victory Points. If both sides have ships within 6”, then the side with the highest Priority Level ship will gain the bonus Victory Points. Neither side will gain the bonus Victory Points if both have ships of equal Priority Level within 6”.
    """),
    "space-superiority": _rules("""
        Source: Rulebook p. 62

        Fleets: Players have random Fleet Allocation Points and choose their fleets freely. Both players are permitted to keep up to half their ships in hyperspace, so long as they have at least one ship in hyperspace with the Jump Engine or Advanced Jump Engine trait.

        Pre-Battle Preparation: Roll for Initiative as normal – the losing fleet will be forced to set up first. The fleets are deployed anywhere in their own deployment zones as shown on the scenario map. Stellar debris is generated randomly.

        Scenario Rules: None.

        Game Length: 12 turns.

        Victory and Defeat: This scenario uses Victory Points in order to determine who wins. However, divide the battlefield up into a grid, where each grid square is 24” by 24”. If a player has at least one ship in a square and no enemy ships, then he gains +5 bonus Victory Points. Crippled ships and those stricken or on a Skeleton Crew may not claim a square in this manner. For the purposes of tactical withdrawal, each short edge is considered to belong to the player who deployed along its length. Long table edges are considered neutral.
    """),
    "supply-ships": _rules("""
        Source: Rulebook p. 63

        Fleets: Players have random Fleet Allocation Points and choose their fleets freely. The defending player also has two corporate freighters. These are the convoy ships he must protect. For every increase in Priority Level above Patrol, the number of corporate freighters increases by two. A Priority Level: War game would therefore have ten corporate freighters. The attacker may keep up to half of his ships in hyperspace, so long as he has at least one ship in hyperspace with the Jump Engine or Advanced Jump Engine trait.

        Pre-Battle Preparation: The defending player deploys his entire fleet around the planet. The attacker then deploys his entire fleet in the area surrounding the planet.

        Scenario Rules: The supply ships are always moved in the End Phase of each turn.

        Game Length: 12 turns, or until either side has withdrawn or has no ships on the table (stricken, destroyed and surrendered ships do not count as viable ships).

        Victory and Defeat: This scenario uses Victory Points in order to determine who wins. The attacking player gains +2 bonus Victory Points for every supply ship he destroys (but no other Victory Points are earned for destroying these ships). The defending player gains +2 bonus Victory Points for every supply ship that survives the battle. If the supply ships make a tactical withdrawal, they are considered to be destroyed with regards to Victory Points – if the attacker manages to force the supply ships out of the system, he will have done a great deal of damage to the defending player’s logistics in this region of space.

        Civilian Fleet Points: If you are using Civilian Fleet Points (see the Fleet Book), then you will earn +2 bonus Victory Points per CFP.
    """),
    "gravity-well": _rules("""
        Source: Powers & Principalities pp. 24-25

        Fleets: Both fleets have three Fleet Allocation Points.

        Pre-Battle Preparation: Roll for Initiative as normal – the losing fleet will be forced to set up first. The fleets are deployed anywhere in their own deployment zones as shown on the scenario map.

        Scenario Rules: The asteroid field is Density 7. Any ship (not fighter flight) that is within the asteroid field during the End Phase and did not perform any Special Actions in that turn may search for the admiral by rolling one dice – a bonus of +1 is added to this roll if any friendly fighter flights are within 6” of the ship and are also within the asteroid field. On the roll of a 6, the admiral’s lifeboat has been found, and he will be immediately transported to the ship.

        If a ship carrying the admiral is boarded by the enemy and its crew completely wiped out, then the admiral may be immediately placed on board any ship friendly to the boarders that is within 6”. In this way, the admiral may change hands several times during the battle.

        In addition, fighting this close to an unstable star will cause its own problems for the fleet. The star’s immense gravity field will cause every ship to be moved 1d6” (roll separately for each) directly towards the star’s table edge before the start of every Movement Phase. Any ship that is within 18” of the star’s table edge in an End Phase will be forced to weather terrible radiation bursts and solar flares. It will automatically suffer 1d3 critical hits.

        Game Length: Until victory conditions are met.

        Victory and Defeat: If a ship finds the admiral and leaves the table by any edge other than the star’s, or by jumping to hyperspace, its player may claim victory. If the ship carrying the admiral is destroyed (or if he is never found), then the battle is a draw.

        Optional: You can experiment with random Fleet Allocation Points in this battle, as you will find they greatly influence the way it is played.
    """),
    "invasion": _rules("""
        Source: Powers & Principalities p. 25

        Fleets: The defending player has five Fleet Allocation Points. The attacking player starts with three Fleet Allocation Points, and receives one more Fleet Allocation Point every turn.

        Pre-Battle Preparation: The defending fleet sets up first and is deployed anywhere in its deployment zone as shown on the scenario map. The attacking fleet moves in from its table edge on the first turn. Stellar debris is generated randomly.

        Scenario Rules: The attacking fleet receives one Fleet Allocation point worth of ships at the start of every turn. These ships move in from the attacker’s table edge. The defending player may not perform any Tactical Withdrawals.

        Game Length: Eight turns.

        Victory and Defeat: The attacker wins if he can wipe out the defender’s fleet. The defender claims (a moral) victory if he has at least one ship (not fighter flight) still on the table without being Stricken.

        Optional: If you fancy a truly epic, Battle of the Line-type clash, consider multiplying the Fleet Allocation Points on both sides. For example, you might decide to fight a battle three times the size, and so the defender would start with fifteen Fleet Allocation Points, and the attacker would start with six, and receive three more every turn. Such epic confrontations are perfect for multiplayer team games – they are a good chance for you to get all your ships on the table.
    """),
    "king-of-the-jump-gate": _rules("""
        Source: Powers & Principalities pp. 26-27

        Fleets: Each player has one Fleet Allocation Point at Raid level.

        Pre-Battle Preparation: Up to eight players may take part in this scenario. Fleets do not deploy on the table, instead moving on from each player’s entry point in their first turn. The first player should start from entry point one, the second from entry point two, and so on. This means that, for example, entry points seven and eight will not be used if just six players are playing.

        Scenario Rules: Players roll Initiative as normal, and move their fleets in the order of the lowest roll upwards, re-rolling any ties. Each player’s entire fleet will be moved at the same time, rather than just one ship. Otherwise, play as normal.

        Game Length: Until all remaining players on the table have achieved their victory conditions.

        Victory and Defeat: The victory conditions for each fleet are randomised on the table below. Players are under no obligation to let their opponents know what their victory conditions are until the end of the game. They simply need to let the other players know when they have achieved their objectives. Otherwise, any player can claim victory simply by having the last ship on the table.

        1 — Let no one else in!: Destroy the jump gate at the earliest opportunity. It has Hull 6+ and Damage 80.
        2 — Prove your strength!: Personally deliver the killing blow to at least two enemy ships.
        3 — Take the jump gate!: Move within 8” of the jump gate and be there at the end of the game.
        4 — Old enemy!: Pick one enemy ship of a Priority Level at least as high as the highest in your own fleet. This ship must be destroyed.
        5 — Grab technology!: Board and capture at least one enemy ship.
        6 — Form an alliance!: Convince at least two other players not to fire on your fleet.

        Note: Players may immediately try to ally with one another in an effort to gang up on others. This is perfectly normal and in keeping with politics in the Babylon 5 universe.

        Optional: This game is suited to clubs or stores where many players can join immediately. For a larger confrontation, raise the Priority Level or allow players two or three Fleet Allocation Points.
    """),
    "on-the-back-foot": _rules("""
        Source: Powers & Principalities p. 28

        Fleets: The attacker has eight Fleet Allocation Points. The defender starts with five Fleet Allocation Points, and receives another five Fleet Allocation Points as reinforcements.

        Pre-Battle Preparation: The defending fleet is deployed first, anywhere within its deployment zone, as shown on the map. The attacking fleet is split into two forces, each of four Fleet Allocation Points. Each will move onto the table in the first turn from opposite short table edges. Stellar debris is generated randomly.

        Scenario Rules: The attacking fleets move in from the short table edges during the first turn. The defender’s reinforcement fleet moves in from his long table edge at the start of the fifth turn.

        Game Length: Twelve turns.

        Victory and Defeat: This scenario uses Victory Points in order to determine who wins. Note that the defender must minimise his losses during the first part of the game, or he risks the attacker earning more Victory Points than it is possible for him to claim himself.
    """),
    "towering-inferno": _rules("""
        Source: Powers & Principalities p. 29

        Fleets: Both fleets have ten Fleet Allocation Points.

        Pre-Battle Preparation: Roll for Initiative as normal – the losing fleet will be forced to set up first. The fleets are deployed anywhere in their own deployment zones as shown on the scenario map. Each fleet may only deploy one Fleet Allocation Point’s worth of ships. Stellar debris is generated randomly.

        Scenario Rules: At the start of every turn after the first, each player must roll one dice for each of his ships yet to appear. On the roll of a 6, the ship will move on to the table from a random table edge during the Movement Phase. Use the scenario map to determine which table edge a ship enters from.

        Game Length: Twelve turns.

        Victory and Defeat: This scenario uses Victory Points in order to determine who wins.

        Optional: For a longer battle, remove the turn limit and play to the last ship standing.
    """),
    "battle-of-the-line": _rules("""
        Source: Rulebook pp. 64-65

        Earth Alliance Fleet: Very few experienced crews are left in the Earth Alliance. The fleet contains six Hyperions, eight Novas, four Olympus’ and 15 Aurora Starfury flights. All ships have a Crew Quality of three.

        Minbari Fleet: The Minbari fleet is battle-hardened and well experienced in killing humans. The fleet contains seven Sharlin warcruisers and 12 Nial fighter flights. All ships have a Crew Quality of five.

        Pre-Battle Preparation: This battle takes place in Earth space so no stellar debris is used. The Earth Alliance is deployed first in its deployment zone. The Minbari player moves one Sharlin through each jump point during the first turn. Nials may follow any and all Sharlins through the jump points and ships may not be kept in reserve in hyperspace.

        Scenario Rules: No special rules.

        Game Length: 6 turns.

        Victory and Defeat: If at least one Earth Alliance ship (not flight) remains on the table after the 6th turn, then the Earth player gains victory – though he is probably still doomed, he has delayed the Minbari long enough for a few more civilian ships to escape. If all the Earth ships have been destroyed, then the Minbari claim victory.
    """),
    "assault-on-ragesh-3": _rules("""
        Source: Rulebook pp. 66-67

        Narn Fleet: The Narn fleet begins the game with two T’Loth assault cruisers (both Crew Quality 4) and six flights of Frazi fighters.

        Centauri Fleet: The Centauri fleet starts with a space station but no fighters are carried on board.

        Pre-Battle Preparation: This battle takes place in Ragesh 3 space so no stellar debris is used with the exception of the planet, as noted on the map. The Colony Station is deployed first, also as shown on the map. The Narn player moves through the jump point during the first turn. Ships may not be kept in reserve in hyperspace.

        Scenario Rules: The Centauri player must make a Crew Quality check (target number 8) at the start of each turn. He may not take any actions at all until he passes this check – the personnel on the station are stunned by the sudden Narn attack and need time to get their station battle ready.

        Game Length: Until victory conditions are met.

        Victory and Defeat: If the Narn fleet is completely destroyed, the Centauri gain total victory. Once the Narn reduce the space station by two damage thresholds, it will automatically surrender, giving victory to the attacking fleet.
    """),
    "quadrant-37": _rules("""
        Source: Rulebook pp. 68-69

        Narn Fleet: A single space station, 2 T’Loth assault cruisers and 12 Frazi flights. All have Crew Quality 4.

        Shadow Fleet: 2 Shadow Ships (Young), both with Crew Quality 5.

        Pre-Battle Preparation: Aside from the planet on the map, no Stellar Debris is used. The Narn fleet is deployed first in its deployment zone. The Shadow player enters the table at any point from hyperspace in the first turn.

        Scenario Rules: The Shadow player gains the Initiative in the first two turns automatically. In the first turn, the Narn fleet may only move – it may not attack or take any Special Actions.

        Game Length: 12 turns, or until the victory conditions have been met.

        Victory and Defeat: This is a simple fight to the death. If one fleet destroys its enemy completely or forces it to withdraw, it can claim victory. Additionally, if the space station has not been reduced to 0 Damage by the end of turn 12 then the Narn fleet wins.
    """),
    "second-battle-quadrant-14": _rules("""
        Source: Rulebook pp. 70-71

        Priority Level: War.

        Fleets: The Centauri player has five Fleet Allocation Points. The Narn player has three.

        Pre-Battle Preparation: Stellar debris is generated randomly though the only planet on the table is the one shown on the map. Re-roll any results that indicate another planet or moon is present. The Narn fleet is placed in its deployment zone, surrounding the planet. The Centauri player moves his fleet onto the table in his first turn from his deployment edge. Neither player is allowed to keep ships in reserve in hyperspace – this is a fight to the death and captains on both sides are eager to play their part in history.

        Scenario Rules: None.

        Game Length: 10 turns.

        Victory and Defeat: The game continues for 10 turns. If by this time any Narn ships survive, the Narn player is awarded the victory – he has bought enough time for at least a few civilians to be evacuated. If the Narn fleet is completely wiped out, victory is awarded to the Centauri.
    """),
    "long-twilight-struggle": _rules("""
        Source: Rulebook pp. 72-73

        Narn Fleet: 7 G’Quan heavy cruisers. War Leader G’Sten is present on one of the G’Quans. All Frazi fighters in the fleet may start the scenario deployed. Three G’Quans have Crew Quality 5 (including G’Sten’s) while the others have Crew Quality 4.

        Shadow Fleet: 5 Shadow Ships (Young), all ships with Crew Quality 6. There is also a space station in orbit around the planet.

        Pre-Battle Preparation: No stellar debris is used, other than the planet shown on the map. The Narn fleet is deployed first in its deployment zone, having just jumped from hyperspace. The Shadow player moves his entire fleet onto the table from his edge in the first turn. Neither player is allowed to keep ships in reserve in hyperspace.

        Scenario Rules: The Narn player is attempting a desperate gamble in this scenario. As such, he may not make any Tactical Withdrawals until he has had at least 5 ships destroyed.

        Game Length: Until victory conditions are met.

        Victory and Defeat: The Shadow player wins by destroying every Narn ship. The Narn player wins by either destroying all the Shadow Ships, or the space station, or by successfully making a Tactical Withdrawal via a jump point with two ships. Anything else is a draw.
    """),
    "fall-of-night": _rules("""
        Source: Rulebook pp. 74-75

        Narn Fleet: 1 G’Quan (the G’Toc) heavy cruiser. Though the G’Toc has a Crew Quality of 5, it is badly damaged. It does not have the Jump Engine trait, nor any Frazi fighters. In addition, it may not use its Heavy Laser Cannon or Energy Mines, has a Speed of 4 and may not use the All Power to Engines! Special Action. The Narn also have the use of the Babylon 5 battle station and two flights of Aurora Starfuries (Zeta Squadron).

        Centauri Fleet: 1 Secundus battlecruiser, with Crew Quality 4.

        Pre-Battle Preparation: No stellar debris is used, other than the planet shown on the map. All ships are placed as shown on the map, facing any direction their players choose.

        Scenario Rules: The Narn player may not open fire with any ships or Auxiliary Craft until one turn after the Centauri have first attacked. Until the Centauri attack, they are assumed to automatically win the Initiative every turn. Once shots are fired, roll for Initiative normally.

        Game Length: Until victory conditions are met.

        Victory and Defeat: The Centauri player wins by destroying the Narn ship. He gains a major victory and crowing rights if he destroys the Narn ship and reduces Babylon 5 by one or more damage thresholds. The Narn player wins if he can exit the G’Toc through the jump gate.
    """),
    "severed-dreams": _rules("""
        Source: Rulebook pp. 76-77

        Babylon 5 Fleet: The Babylon 5 player has two Omega destroyers (the Alexander and the Churchill) and Babylon 5 battle station. The Churchill has two flights of Thunderbolts as part of its normal complement. The Churchill has a Crew Quality score of 5, while the Alexander has a Crew Quality score of 6. Due to damage already suffered, both the Alexander and the Churchill begin with only 35 Damage and 45 Crew remaining.

        Earth Alliance Fleet: The Earth Alliance player has two Omega destroyers (the Agrippa and the Roanoke), two Hyperion cruisers (the Cronus and Deimos) and two wings of Breaching Pods. Both the Agrippa and the Roanoke have two flights of Thunderbolts as part of their normal complements. All ships have a Crew Quality score of 4.

        Pre-Battle Preparation: This battle takes place in Babylon 5 space so no stellar debris is used. The Babylon 5 fleet is deployed first in its deployment zone, as shown on the map. The Earth Alliance player moves through the Jump Gate during the first turn. Neither player is allowed to keep ships in reserve in hyperspace – all cards are on the table in this fight of ideologies. However, both fleets may deploy all their fighters before the start of the battle. The Earth Alliance player automatically has the initiative in the first turn.

        Scenario Rules: The Babylon 5 player has a +1 Initiative bonus, as he is technically an Earth Alliance fleet, bringing his total Initiative bonus to +3 including the aid that Babylon 5 itself gives. Note that while Sheridan is present, the rules for using Captain Sheridan on board a ship are not – they reflect his abilities as a warship officer, not the military governor of a small city in space.

        Game Length: Until victory conditions are met.

        Victory and Defeat: This scenario is a straight fight to the death. The Babylon 5 player wins if he can destroy the Earth Alliance fleet or force them to withdraw. The Earth Alliance fleet wins if it can destroy the two opposing Omegas, all of Babylon 5’s fighter flights that are launched and reduce Babylon 5 to at least its first damage threshold.
    """),
    "interludes-and-examinations": _rules("""
        Source: Rulebook pp. 78-79

        Priority Level: War.

        Vorlon Fleet: 1 Vorlon Heavy Cruiser, 8 Vorlon Destroyers and 8 Vorlon Fighter flights. Roll for random Crew Quality for each.

        Shadow Fleet: 4 Shadow Ships (Young) and 4 Shadow Fighter flights. Roll for random Crew Quality for each.

        Pre-Battle Preparation: Stellar debris can be randomly generated if both players wish but no planets should be used. The Shadow fleet is deployed first in its deployment zone. The Vorlon player moves his entire fleet onto the table from a single jump point placed anywhere he desires outside of the Shadows’ deployment zone in the first turn. Neither player is allowed to keep ships in reserve in hyperspace.

        Scenario Rules: Only the Vorlons may attack in the first turn. The Shadows may move but cannot do anything else unless Vorlon Fighters contact Shadow Fighters, in which case the dogfight is resolved as normal. The Vorlons automatically win the Initiative in the first turn.

        Game Length: Until one fleet is destroyed or withdraws.

        Victory and Defeat: Victory Points are used as normal to gauge who wins this scenario.
    """),
    "shadow-dancing": _rules("""
        Source: Rulebook pp. 80-81

        Priority Level: War.

        Army of Light Fleet: 4 Minbari Sharlins, 6 Minbari Nial flights, 4 Brakiri Avioki, 8 White Stars, 4 Drazi Warbirds, 2 Drazi Sunhawks, 6 Drazi Sky Serpents, 2 Vree Xills, and 1 Narn G’Quan. Roll for random Crew Quality for each. Each Sharlin carries Telepaths and is able to attempt to jam up to 3 Shadow vessels each turn. In addition, Commander Ivanova is present in a White Star, currently awaiting repairs after a confrontation with a Shadow Scout. Her White Star has a Crew Quality of 6.

        Shadow Fleet: 10 Shadow Ships (8 Young, 2 Ancient), 4 Shadow Scouts and 20 Shadow Fighter flights. Roll for random Crew Quality for each.

        Pre-Battle Preparation: Stellar debris can be randomly generated if both players wish but no planets should be used. The Shadow fleet is deployed first in its deployment zone, then Commander Ivanova’s White Star is placed as shown on the map. The Army of Light player moves his entire fleet onto the table from six Jump Points placed anywhere in his deployment zone during the first turn. Neither player is allowed to keep ships in reserve in hyperspace.

        Scenario Rules: Commander Ivanova’s White Star is currently undergoing repairs and cannot take any actions – it will remain immobile and unable to attack (or Dodge!). Make a Crew Quality check in every End Phase. When a 10 or more is scored, the White Star becomes active and may move and attack as normal. Until this happens, it is assumed to be Running Silent and so has a Stealth score of 4+.

        Game Length: Until one fleet is destroyed or withdraws.

        Victory and Defeat: Victory Points are used as normal to gauge who wins this scenario.
    """),
    "into-the-fire": _rules("""
        Source: Rulebook pp. 82-83

        Priority Level: War.

        Army of Light Fleet: The Army of Light player has 12 White Stars, all with Crew Quality 5. Some or all of these may be swapped for White Star II’s. In addition, one of these White Stars will be carrying Captain Sheridan himself.

        Vorlon Fleet: The Vorlon fleet has just a space station. Because of the way space stations operate, it is presumed that this scenario will be played as a solo match, with the Army of Light player matching his skills against potent Vorlon technology.

        Pre-Battle Preparation: This battle takes place in deep space so stellar debris is generated normally. The Vorlon space station is placed first, as shown on the map. The Army of Light fleet is then placed in the deployment zone. Ships may not be kept in reserve in hyperspace – it is assumed that Sheridan’s forces have just exited hyperspace and are now committed to the attack.

        Scenario Rules: If this scenario is played as a solo game, the Vorlon space station will automatically target each White Star within range every turn, up to its Targets score. The Vorlon space station has the Adaptive Armour and Self-Repairing 3D6 traits. Each weapon system gains the Triple Damage trait.

        Game Length: Until victory conditions are met.

        Victory and Defeat: This scenario is a straight fight to the death. The Army of Light player wins if he can reduce the Vorlon space station to 0 Damage. He will gain a draw if he reduces the space station to its last damage threshold. Anything else is a victory for the Vorlons.
    """),
    "between-darkness-and-light": _rules("""
        Source: Rulebook pp. 84-85

        Priority Level: War.

        Army of Light Fleet: 22 White Stars (these may be original White Stars, White Star II’s, or a mix of the two). Roll for random Crew Quality for each. Commander Ivanova’s White Star automatically has a Crew Quality of six.

        Psi Corps Fleet: Eight Shadow Omegas. Each has a Crew Quality of five.

        Pre-Battle Preparation: Stellar debris can be randomly generated if both players wish but no planets should be used. The Army of Light fleet is deployed first in its deployment zone. The Earth Alliance player moves his entire fleet onto the table, using one jump point for each ship, placed anywhere in his deployment zone during the first turn. Each jump point has to be within 6” of another. Neither player is allowed to keep ships in reserve in hyperspace. The Earth Alliance player may not begin the game with his Thunderbolts deployed but may launch them later on.

        Scenario Rules: None – this is a straight up fight between two large fleets!

        Game Length: Until one fleet is destroyed or withdraws.

        Victory and Defeat: Victory Points are used as normal to gauge who wins this scenario.
    """),
    "border-dispute": _rules("""
        Source: Rulebook p. 76

        Brakiri Fleet: 1 Halik Frigate (Crew Quality 4), 2 Ikorta Light Assault Cruisers (Crew Quality 3).

        Drazi Fleet: 4 Sunhawk Battlecruisers (Crew Quality 3), 2 Warbird Cruisers (Crew Quality 4).

        Pre-Battle Preparation: Roll for Initiative before deployment. The loser deploys his entire fleet first. The winner then deploys his entire fleet. Stellar debris is generated randomly.

        Scenario Rules: No actual weapons will be fired during the initial phases of the battle. Instead, a ship may target another that is in range as if it were about to fire. It will automatically deal one point of Damage for every AD it can place on a target (doubled for Double Damage weapons, tripled for Triple Damage weapons). However, this is not actual Damage and no Critical Hits are dealt – it is strictly a measure of the strength of a ship’s position in the mock battle and the lock-ons it achieves. If a ship is reduced to 0 Damage in this way, it must make a Tactical Withdrawal as soon as possible.

        Game Length: 12 turns.

        Victory and Defeat: The battle continues until one fleet has been forced to make a Tactical Withdrawal. The victor is the fleet that gains the most Victory Points. However, either fleet may choose to make this a real battle at any point. Instead of simply mock reducing a target’s Damage score by the number of AD that can be placed upon it, real shots may be fired instead. When this happens, every ship that has taken mock Damage automatically has its Damage score restored to normal. Every attack from now on is made as normal, rolling dice and calculating actual damage. The winner will be the fleet that accrues the most Victory Points.
    """),
    "hunting-the-hunters": _rules("""
        Source: Rulebook p. 77

        ISA Fleet: 1 White Star (Crew Quality 6).

        Raiders Fleet: 1 Battlewagon (the Timber Wolf, Crew Quality 2), 1 Strike Carrier (the Kodiak, Crew Quality 3).

        Pre-Battle Preparation: The Raiders player deploys his ships. The ISA player can enter the battle anywhere on the table via a jump point during any turn. No fighters may be deployed by either side until the turn after the White Star is placed on the table. Stellar debris is generated randomly.

        Scenario Rules: No special rules are used.

        Game Length: Until victory conditions are met.

        Victory and Defeat: The ISA player wins if he can prevent both Raiders’ ships from leaving the exit edge of the table. The Raiders player wins if he can destroy the White Star or if he can move both ships off the exit edge.
    """),
    "initial-contact": _rules("""
        Source: Powers & Principalities pp. 31-32

        Tournament Fleet Restriction: Each fleet comprises one Skirmish level ship and one Battle level ship. All ships have Crew Quality 4; ISA, Gaim and Vree ships receive their usual bonuses.

        Fleets: Both players start with their Skirmish level ships.

        Pre-Battle Preparation: Roll for Initiative – the losing fleet will be forced to set up first. The fleets are deployed anywhere in their own deployment zones as shown on the scenario map.

        Scenario Rules: Both patrolling ships immediately send a distress signal. At the start of Turn 5, both players roll a dice – on a 4 or more, their Battle level ship arrives, moving on from their own table edge. If a Battle ship fails to appear on Turn 5, it automatically appears at the beginning of Turn 6. If a Skirmish level ship is destroyed before its Battle level counterpart arrives, the Battle level ship aborts its mission and does not arrive.

        Game Length: Until one fleet withdraws or either side has no ships on the table (Running Adrift, destroyed and surrendered ships do not count as viable ships).

        Battle Grades:
        Outstanding — Destroy the enemy Skirmish ship before any Battle level ship arrives, or destroy both enemy ships without losing one of your own.
        Good — Destroy at least one enemy ship without losing one of your own.
        Adequate — Destroy at least one enemy ship.
        Poor — Any other result.
    """),
    "automaton-recovery": _rules("""
        Source: Powers & Principalities pp. 32-33

        Tournament Fleet Restriction: Each fleet comprises one Skirmish level ship and one Battle level ship. All ships have Crew Quality 4; ISA, Gaim and Vree ships receive their usual bonuses.

        Fleets: Both players start with their entire fleets.

        Pre-Battle Preparation: Each player takes three counters and takes turns placing them anywhere on the table. Each must be placed at least 12” from a table edge and at least 6” away from another counter. None may be placed on the planet. These represent the drones that must be recovered. Next, roll for Initiative – the losing fleet will be forced to set up first. The fleets are deployed anywhere in their own deployment zones as shown on the scenario map.

        Scenario Rules: To take a drone on board, a ship must pass within 1” of it and perform a Recover Drone Special Action. This Special Action requires no Crew Quality check, but the ship may not fire any weapons or use any traits for that turn. A ship may only pick up one drone in a single turn.

        Game Length: Until one fleet withdraws or either side has no ships on the table (Running Adrift, destroyed and surrendered ships do not count as viable ships).

        Battle Grades:
        Outstanding — Recover at least 5 drones.
        Good — Recover at least 3 drones.
        Adequate — Recover at least 2 drones.
        Poor — Any other result.
    """),
    "first-strike": _rules("""
        Source: Powers & Principalities pp. 33-34

        Tournament Fleet Restriction: Each fleet comprises one Skirmish level ship and one Battle level ship. All ships have Crew Quality 4; ISA, Gaim and Vree ships receive their usual bonuses.

        Fleets: Both players start with their entire fleets.

        Pre-Battle Preparation: Roll for Initiative – the losing fleet will be forced to set up first. The fleets are deployed anywhere in their own deployment zones as shown on the scenario map, with the Battle level ships close to the planet and the Skirmish level ships further away.

        Scenario Rules: Both Battle level ships have overloaded systems. Whenever firing a weapon system on the Battle level ship, roll a dice. On a 5 or more, the weapon fires normally; on any other result it does not fire. Whenever a flight is launched, roll a dice. On a 5 or more, it launches normally; on any other result, problems in the hangars cause a delay and it is not launched.

        Game Length: Until one fleet withdraws or either side has no ships on the table (Running Adrift, destroyed and surrendered ships do not count as viable ships).

        Battle Grades:
        Outstanding — Destroy both enemy ships without losing one of your own.
        Good — Destroy at least one enemy ship without losing one of your own.
        Adequate — Destroy at least one enemy ship.
        Poor — Any other result.
    """),
    "shadows-of-the-past": _rules("""
        Source: Powers & Principalities pp. 34-35

        Tournament Fleet Restriction: Each fleet comprises one Skirmish level ship and one Battle level ship. All ships have Crew Quality 4; ISA, Gaim and Vree ships receive their usual bonuses.

        Fleets: Both players start with their entire fleets.

        Pre-Battle Preparation: Roll for Initiative – the losing fleet will be forced to set up first. The fleets are deployed anywhere in their own deployment zones as shown on the scenario map.

        Scenario Rules: To get the Commando unit on the enemy Battle level ship, perform a single successful boarding action, ensuring at least one Troop is alive on the enemy ship at the end of the turn. The commando unit is carried on your Skirmish level ship. Vorlon and Shadow ships may be boarded in this manner, though any Troops that make it on board are each automatically destroyed on the roll of a 3 or more.

        Game Length: Until either side has no ships on the table (Running Adrift, destroyed and surrendered ships do not count as viable ships).

        Battle Grades:
        Outstanding — Get a commando on board the enemy Battle level ship, then withdraw both of your ships without them being Crippled.
        Good — Get a commando on board the enemy Battle level ship, then withdraw at least one of your ships, whatever its condition.
        Adequate — Get a commando on board the enemy Battle level ship.
        Poor — Any other result.
    """),
}
