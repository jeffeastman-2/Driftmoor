# Driftmoor v0.1 Known Limitations

Driftmoor v0.1 is a self-hosted, town-focused vertical slice for one human
player per game-server process. It is not an authenticated public service.

- The Fey Glade and Echoing Caverns are experimental previews; their content is
  not covered by the town release guarantee.
- The Old Mill, the Haverstad family promotion, and broader regional campaign
  progression are unfinished.
- Public-internet hosting, accounts, lobbies, player seat assignment, and
  multiple independently authenticated humans are unsupported.
- Some services use authored ranges, donations, barter, or negotiation rather
  than a fixed price. Goods with a numeric listed price use engine-enforced
  settlement; other services may be narrated and adjudicated by the DM.
- LLM narration can still vary by provider and model. Engine state remains
  authoritative when narration and resolved movement or commerce disagree.
- Checkpoints and transcripts intentionally contain game input and narration.
  Treat `runtime/` as private player data; it is excluded from Git.

Users are responsible for access controls around remotely reachable game or
model endpoints. Keep them on localhost or a trusted private network; a reverse
proxy or tunnel alone does not supply application authorization.
