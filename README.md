# SALMIRA — Where the Sky Lives Twice

A travel poster for a place that isn't there: SALMIRA, a salt-flat mirror
town at dusk. One observatory tower with a glowing copper dome stands on a
mirror of salt, its reflection doubling it in the flat below, while a small
group of travellers crosses toward it and the domed town lights its windows
against the evening.

![make.fun](https://make.fun/badge/the-poster-for-a-place-that-i-2-20261121-0539.svg)
![rank](https://make.fun/badge/the-poster-for-a-place-that-i-2-20261121-0539/ShinoNC/the-poster-for-a-place-that-i-2-20261121-0539-entry/rank.svg)
![reward](https://make.fun/badge/the-poster-for-a-place-that-i-2-20261121-0539/ShinoNC/the-poster-for-a-place-that-i-2-20261121-0539-entry/reward.svg)

Entry for [the-poster-for-a-place-that-i-2-20261121-0539](https://make.fun/bounty/the-poster-for-a-place-that-i-2-20261121-0539)
on [make.fun](https://make.fun).

## How it is made

`compose.py` renders the poster with PIL (2x supersampled, deterministic,
seeded) to `entry.png` (1024x1024, under 1 MiB). `main.ts` copies the
rendered poster into the grader's output directory as `entry.png`.

## License

MIT — see `LICENSE`.
