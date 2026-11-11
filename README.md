# Fantic OEM setup pack for MX Bikes

Eight garage setup sheets for the Fantic bikes in the MX OEM pack: XXF 450 and XXF 250 (each for MX, SX and SMX), plus the XX 125 and XX 250 two-strokes. Every value is a normal garage setting. Nothing here touches bike, engine or server physics files.

## Read this first: the game does not load these files

MX Bikes saves setups as **binary** `.stp` files, not INI text. A `.stp` stores each setting as a position in that bike's option list, tagged with the bike's internal ID and version, and the game rejects a file whose tag does not match. A text file dropped into the setups folder is ignored.

So these `.ini` files are setup sheets to dial in by hand:

1. Pick the bike, go to the track, open the garage.
2. Set each value from the sheet. The sections follow the garage pages (see the key below).
3. Save the setup under a name. The game writes a valid `.stp` to `Documents\PiBoSo\MX Bikes\profiles\<profile>\setups\`.
4. Use the garage **Copy** button to reuse it on other tracks.

## The pack

| File | Gearing | Fork offset | Fork height | Rod length | Race sag |
|---|---|---|---|---|---|
| `setups/XXF450/XXF450_MX.ini` | 13/50 | 24 mm | 2 mm | 144 mm (max) | 105 mm |
| `setups/XXF450/XXF450_SX.ini` | 13/50 | 22 mm | 4 mm | 144 mm (max) | 102 mm |
| `setups/XXF450/XXF450_SMX.ini` | 13/50 | 22 mm | 0 mm (min) | 144 mm (max) | 103 mm |
| `setups/XXF250/XXF250_MX.ini` | 13/51 | 24 mm | 2 mm | 144 mm (max) | 104 mm |
| `setups/XXF250/XXF250_SX.ini` | 13/52 | 22 mm | 4 mm | 144 mm (max) | 102 mm |
| `setups/XXF250/XXF250_SMX.ini` | 13/51 | 22 mm | 0 mm (min) | 144 mm (max) | 103 mm |
| `setups/2T/XX125_2T.ini` | 13/52 | 24 mm | 2 mm | max slot | 102 mm |
| `setups/2T/XX250_2T.ini` | 13/50 | 24 mm | 2 mm | max slot | 103 mm |

## Key

| Sheet key | Garage page | Unit and direction |
|---|---|---|
| `Map` | Others | Engine mapping. Pick the most aggressive entry. If there is no selector, the bike has one map. |
| `FrontSprocket`, `RearSprocket` | Drivetrain | Teeth. Fewer front or more rear = shorter gearing. |
| `SpringRate` | Suspensions | N/mm. |
| `Preload` | Suspensions | mm. A starting number: adjust it until the sag readout matches. |
| `OilLevel` | Suspensions | mm of air gap above the oil. **Lower number = more oil** = more bottoming resistance. |
| `Compression`, `Rebound`, `LowSpeedCompression` | Suspensions | Clicks out from fully closed. Lower = firmer or slower. |
| `HighSpeedCompression` | Suspensions | Turns out from closed. 1.25 shows as `1-1/4`. |
| `RaceSag` | Suspensions | mm, with the sag readout set to Race (rider on). Set it with rear preload. |
| `ForkHeight` | Others | mm of fork tube above the clamp. Lower = taller front = more stable. |
| `ForkOffset` | Others | mm. The OEM manual treats more offset as more stable, less as more agile. |
| `RodLength` | Others | mm. Longer = lower rear. |
| `FrontPressure`, `RearPressure` | General | bar. Lower = more grip, less rim protection. |
| `[GarageLimits]` | | Fields to run at the garage limit, whatever number that limit is on your install. |

`Name` is a label in the style of the brief. It is not the bike's internal ID.

## How far to trust each number

I could not open the OEM pack, so I have not seen the option lists these bikes offer. Snap every value to the nearest option your garage shows.

- **From the brief:** gearing, fork offset (24 and 22), fork height, rod length (144) and the 102-105 mm sag window. I assumed these exist in your garage.
- **From the real bikes:** spring rates and clicker baselines come from the Yamaha YZ platform the Fantics are built on (450: 5.0 fork, 58 shock; 250F: 4.7, 56; 125: 4.3, 48; 250 2T: 4.5, 50).
- **My estimates:** oil level, preload and tyre pressures, and the SX "max" fork spring. I do not know these ranges.

If your garage uses a different scale, apply the same moves relative to the bike's default:

| Field | MX and 2-T | SX | SMX |
|---|---|---|---|
| Fork spring | default | maximum | default + 2 steps |
| Fork oil | 2 steps more oil | maximum oil (lowest mm) | 1 step short of maximum |
| Fork compression | 0-1 click firmer | 4-5 clicks firmer | 5-6 clicks firmer |
| Fork rebound | default | 2 clicks slower | 3 clicks slower |
| Shock spring | default | + 2 steps | + 1 step |
| Shock low-speed compression | default | 3-4 clicks firmer | 3-4 clicks firmer |
| Shock high-speed compression | default | 1/4-1/2 turn firmer | 1/4 turn firmer |

Where a range is given, the larger move is for the 450.

## Where I departed from the brief

- **No 11/50 on the 450.** Against the real stock 13/49 it is 21% shorter and gives up 17% of top speed in every gear, which means wheelspin and the limiter everywhere. An 11-tooth front is also unlikely to be on the list. 13/50 is 2% shorter than stock. If you want more, go to 13/51 before touching the front sprocket.
- **Sprockets do not close the gap between 2nd and 3rd.** That gap is fixed by the gearbox. Shorter final drive moves every gear down together, so you reach 3rd sooner.
- **SMX uses the motocross bike.** I could not confirm a Fantic in the supermoto OEM packs, so the SMX sheets are for the MX1 and MX2 OEM bikes on hybrid tracks, with knobby-tyre pressures. On a dedicated supermoto bike, keep that tyre's default pressures and use the relative table above.
- **"Lowest possible fork height" is read as the lowest value (0 mm, forks flush).** That gives the tallest, most stable front under tarmac braking. If it will not turn in, raise the forks 2 mm at a time.
- **Two-stroke rod length.** The 144 mm figure is from the XXF chassis. On the XX 125 and XX 250 use the longest slot listed.
- **Anti-stall is gearing and clutch.** Nothing else in the garage affects stalling. The two-stroke sheets use 13/52 (125) and 13/50 (250), which are 6% and 8% shorter than real stock. If the 250 only spins, 14/52 is the milder step.

## Adjusting from telemetry

| What you see | Change |
|---|---|
| On the limiter before the braking point of the longest straight | 1 tooth off the rear |
| Never reaching top gear | 1 tooth onto the rear |
| Fork bottoms on landings | More oil first, then compression 2 clicks firmer, then the next spring |
| Front bounces after braking on tarmac | Fork rebound 1-2 clicks slower |
| Front pushes or tucks on corner entry | Rod length 1 slot shorter, or forks up 1-2 mm, or offset 1 step lower |
| Headshake at speed | Forks down toward flush, sag toward 105 mm |
| Rear kicks in whoops or off jump faces | Shock rebound 1-2 clicks slower, high-speed compression 1/4 turn softer |
| Rear packs down through whoops | Shock rebound 1-2 clicks faster |
| Rear spins on exit | Rear pressure down 0.05 bar, low-speed compression 2 clicks softer |

Two settings are left off the sheets. Fuel: carry the smallest load that finishes the race plus one lap. Swingarm length: leave it at default, and go one step longer if the bike loops out on exits.

## Sources

- [mx-bikes-rust-engine](https://github.com/fent700/mx-bikes-rust-engine): reverse-engineered `.stp` layout and the garage field list
- [mxb-app changelog](https://github.com/Frostn1/mxb-app/blob/main/CHANGELOG.md): setup version tagging and the geometry settings
- [MX OEM manual](https://oem.mxb-mods.com/manual/): oil level and fork offset definitions
- [MX OEM v0.18.1](https://oem.mxb-mods.com/mx-oem-v0-18-1-second-wave/) and [v0.18.2](https://oem.mxb-mods.com/mx-oem-v0-18-2-release/): Fantic models and classes
- [MX Bikes troubleshooting guide](https://gist.github.com/thomas4f/1fd379fafb4ab402b48424ae1c9cf2bd): setups folder location
- [Keefer Inc. Testing](https://www.keeferinctesting.com/2022-250-mx-suspension-baseline-settings/): real-bike baseline settings
