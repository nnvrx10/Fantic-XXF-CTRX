# Garage files

The `.stp` files cannot be built without these. They come from your own copy of MX Bikes: the bike's internal ID and the range of each setting are not published anywhere the converter can read.

Start with one bike (the XXF 450) so the converter can be checked against your game before you do the rest.

## What to upload, per bike

Save three setups in the garage:

| Setup name | How to make it |
|---|---|
| `template` | The bike's default setup, with the engine map and tyres you want to race. |
| `left` | Start from `template`, then click every setting listed below as far **left** as it goes. |
| `right` | Start from `template`, then click every setting listed below as far **right** as it goes. |

Settings to click through:

- Drivetrain: front sprocket, rear sprocket
- Fork: spring, preload, oil level, compression, rebound
- Shock: spring, preload, low-speed compression, high-speed compression, rebound
- Geometry: fork height, fork offset, rod length
- Tyres: front pressure, rear pressure

With each setup loaded, take a screenshot of every garage page that shows those settings.

Then upload to this folder:

- the three `.stp` files, renamed with the bike in front: `XXF450_template.stp`, `XXF450_left.stp`, `XXF450_right.stp`
- the screenshots, with the bike and setup in the name, such as `XXF450_left_suspension.png`

The saved `.stp` files are under `Documents\PiBoSo\MX Bikes\profiles\<profile>\setups\`.

## Bike prefixes

| Bike | Prefix |
|---|---|
| Fantic XXF 450 | `XXF450` |
| Fantic XXF 250 | `XXF250` |
| Fantic XX 125 | `XX125` |
| Fantic XX 250 | `XX250` |
