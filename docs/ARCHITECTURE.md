# Architecture

Dungeon Assist separates simulation from narration. Engines own structured campaign state; an LLM layer may later explain or roleplay that state. Canon-changing generated events require DM approval.

Planned engines include relationships (friendship/love/hate), factions, reputation, rumors, encounters, NPCs, world advance, causality/events, and DM-only knowledge.

Reset is deliberately destructive and therefore locked by default. The intended flow is unlock -> two-minute window -> exact campaign-name confirmation -> automatic recovery snapshot -> reset.
