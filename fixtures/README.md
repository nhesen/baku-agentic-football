# Input fixtures

`new-home.json` adapts the public MIT-0 AWS sample test state, inspected in the
Vienna repository at commit `c56b6c2f6dc6649776a18de68c472bb2c97daee8`:
https://github.com/philippru/vienna-stars-agentic-football/blob/c56b6c2f6dc6649776a18de68c472bb2c97daee8/lib/test_helpers.py

`old-away.json` is a synthetic mirrored equivalent using the older
`playerId/teamId/possessionPlayerId` schema. `loose-ball.json` is a synthetic free-ball
variant. None is represented as a captured payload from the Baku event.

Both sides repeat numeric player IDs. Never identify possession by index alone.
The fixture licence is MIT-0; see the retained deployment template licence.
