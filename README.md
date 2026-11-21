# SALMIRA — Where the Sky Lives Twice

![make.fun](https://make.fun/badge/the-poster-for-a-place-that-i-2-20261121-0539.svg)
![rank](https://make.fun/badge/the-poster-for-a-place-that-i-2-20261121-0539/ShinoNC/the-poster-for-a-place-that-i-2-20261121-0539-entry/rank.svg)
![reward](https://make.fun/badge/the-poster-for-a-place-that-i-2-20261121-0539/ShinoNC/the-poster-for-a-place-that-i-2-20261121-0539-entry/reward.svg)

A travel poster for a place that isn't there: SALMIRA, a salt-flat mirror
town at dusk. One observatory tower with a copper dome and a beacon stands
alone on a mirror of salt, its reflection doubling it in the flat below,
while five robed travellers cross toward the lit town on the horizon.

Entry for [the-poster-for-a-place-that-i-2-20261121-0539](https://make.fun/bounty/the-poster-for-a-place-that-i-2-20261121-0539)
on [make.fun](https://make.fun).

## How it is made

`compose.py` draws the poster with PIL at 2x supersample — numpy sky and
water gradients, blurred glow layers for the sun, beacon and lit windows,
layered grain, brush-dab texture, a wave-distorted mirror reflection of
the town and tower, faceted salt crystals, and robed travellers with long
soft shadows. The render is deterministic: same input, same bytes.

`main.ts` copies the rendered `entry.png` into `$MAKEFUN_OUTPUT_DIR`.

## Files

- `entry.png` — the poster, 1024x1024
- `compose.py` — the renderer
- `main.ts` — the entrypoint
- `LICENSE` — MIT

## License

MIT — see `LICENSE`.
