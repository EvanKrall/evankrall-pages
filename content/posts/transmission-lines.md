---
title: "Why do EDA programs only draw half of the transmission line?"
date: 2022-12-16T21:27:00-08:00
draft: true
---

_**tl;dr:** For high-speed signals, EDA programs should provide a mode where you can simultaneously route a signal trace on one layer and a wider ground/power trace for the signal's return current on an adjacent layer, directly under the signal trace; essentially routing a whole microstrip transmission line._

# What's a return current path?

If you aren't familiar with designing high-speed digital circuits, you might think of digital signals as time-varying voltages, and not think much about current.
After all, digital input pins are often high-impedance, meaning they draw negligible current.
However, with higher frequency signals, capacitance in your circuit means that the transmitter needs to push or pull nonzero current into/out of the wire to get the voltage on the line to change, even if the receiver has a high-impedance input.
Furthermore, to reduce the possibility of [signal reflections](https://en.wikipedia.org/wiki/Reflections_of_signals_on_conducting_lines) that distort the incoming signal, high-speed receivers will typically have somewhat low input impedance of e.g. 50 to 200 ohms, which allows nonzero current to flow.
For example, [LVDS](https://en.wikipedia.org/wiki/Low-voltage_differential_signaling) signaling tends to pass about 3.5mA.

All this current **must return to the transmitter somehow**, as all current must flow in a loop.
This loop will typically consist of:

 - The power supply and/or decoupling capacitors near your transmitter
 - The the transistors in the transmitter's output stage
 - The signal trace from transmitter to receiver
 - The receiver's input stage, which may include a resistor to ground or a reference voltage
 - The receiver's reference voltage source
 - The ground conductors between transmitter and receiver

{{<
    figure caption="Simplified schematic diagram for a digital transmitter and receiver, showing the current flow for a rising edge. In this model, I'm assuming that the V<sub>CC</sub> connection between transmitter and receiver has higher inductance than the ground connection, which would be the case if V<sub>CC</sub> is handled by traces and ground is handled by a copper pour. Additionally, I'm assuming that the battery has higher inductance than the decoupling capacitor for the transmitter."
    src="/img/transmission-lines/signal_flow.png"
    >}}

You may be familiar with the maxim that current follows the path of least resistance.
(In reality, it follows _all_ parallel paths, with current inversely proportional to resistance.)
To be more accurate, we have to say that current follows the path(s) of least [impedance](https://en.wikipedia.org/wiki/Electrical_impedance), which generalizes the concept of resistance to describe how current flows in circuits with capacitance and inductance.
Any wire or PCB trace has nonzero inductance, which affects impedance more and more as frequency increases, causing inductance to have much stronger effects than resistance at high frequencies.

Since the inductance of a loop of wire decreases as you decrease the area traced by the loop, high-frequency signals will tend to follow a path that has the least cross-sectional area possible;
that is, the return current "wants" to travel in a path that's as close as possible to the outgoing current.
(It also wants to spread out a bit, as a wider conductor has lower inductance than a narrower conductor.)
If your circuit board has a [ground plane](https://en.wikipedia.org/wiki/Ground_plane#Printed_circuit_boards) below your signal trace, the return current will tend to follow a path directly underneath the signal trace, but spread out slightly.

{{< figure
    caption="The faint lines show the approximate path of the return current through a ground plane beneath a trace carrying a high-speed signal."
    src="/img/transmission-lines/current_path_on_ground_plane.png"
    >}}

If you don't have a ground or power plane, and instead use traces to connect ground/power between your different ICs, then the return current for your signal will tend to travel in the ground/power traces nearest to the signal trace.
This tends to lead to higher inductance and a less consistent impedance as the signal propagates through the trace.
Impedance changes can cause your signal to be reflected, distorting the signal that your receiver sees.
The increased loop area traced out by your signal/return path will lead to [Electromagnetic interference (EMI)](https://en.wikipedia.org/wiki/Electromagnetic_interference) and [cross-talk](https://en.wikipedia.org/wiki/Crosstalk) between nearby signals.

Thus, the best practices for routing high-speed signals on a PCB include:

 - Have a ground plane on a PCB layer adjacent to the signal trace
 - Don't route signal traces over breaks in the ground plane
 - Connect your transmitter and receiver ICs to the ground plane with low-impedance (short and wide) connections
 - If you need to move a signal to a different layer by using [vias](https://en.wikipedia.org/wiki/Via_%28electronics%29), you should also include a way (more vias) for the return current to move to the ground plane closest to that other layer.

(Power planes may also provide a good return path, in certain circumstances, but it seems like experts recommend trying to use ground planes if possible.<!-- insert link to Rick Hartley video here -->)

This combination of signal trace + ground plane forms a [microstrip](https://en.wikipedia.org/wiki/Microstrip) transmission line.

{{< figure width=100% src="/img/transmission-lines/Microstrip_geometry.svg" caption="Cross-section of a microstrip transmission line. The area marked `A` is the signal trace, and `D` is the ground plane." >}}

# The current workflow

EDA software such as [KiCad](https://KiCad.org) lets you build transmission lines for your high-speed signals out of primitive components (traces, vias, and filled zones). Superficially, it's pretty straightforward to construct a transmission line manually:

- create a ground (or power) plane by drawing a filled zone on the first inner layer
- make sure both the receiver and transmitter are connected to that plane with short+wide traces
- draw your signal trace on the top layer

(I'm assuming a 4-layer board in these examples, with inner layers used for planes, and outer layers used for traces.)

However, the devil is in the details:

## Holes in the plane

What if power/ground plane has a hole or slot in it for some reason?
For example, if your design has a [split ground plane](https://resources.pcb.cadence.com/blog/2021-should-you-ever-separate-analog-and-digital-ground-planes) (seems like most experts recommend against this these days), multiple filled zones handling different power supply voltages, or you've routed a trace on that inner layer.
Maybe you have a via for another trace nearby -- the clearance rules for the filled zone will create a hole in the zone centered on the via.
Even worse, if you have vias on either side of your trace, and the clearance circles for the two vias overlap underneath your trace.


{{<
    figure caption="Example showing two nearby vias creating a slot in the ground plane, and a single via creating a hole. Return current for the signal will have to divert around these obstructions."
    src="/img/transmission-lines/close_vias_ground_plane.png"
    >}}
It's simpler if you can constrain yourself to routing the signal trace on top of an unbroken ground plane, but if that's not possible, you can provide a path for your return current with stitching capacitors: connect the two filled zones (or sides of the split) with a capacitor.

## Switching sides

If you need to send your signal to the other side of the board, you can use a via.
However, you also need to provide a path for the return current to move between your two inner layers.
If you've got a ground plane on both inner layers, you just need another via, placed near the signal via.

{{< figure
    caption="A nearby via connecting the two inner-layer ground planes together allows the return current to travel to the other ground plane as the signal switches sides of the board."
    src="/img/transmission-lines/ground_via.png"
    >}}

If your filled zones on the two layers are different nets (e.g. power on one layer, ground on the other), then you'll need to add a stitching capacitor.

{{< figure
    caption="With the two inner layers not directly connected, the return current will need to travel through a capacitor."
    src="/img/transmission-lines/stitching_capacitor_power_plane.png"
    >}}

# How EDA tools could do better

I think KiCad and other EDA tools could make our lives easier by adding functionality for directly creating transmission lines by routing two traces simultaneously: one for the signal, one for the return current.
This would work similarly to how differential pair routing works, except instead of drawing two traces side-by-side, it would draw the two traces on adjacent layers, with one larger than the other.

The trace for the return current should be wide enough that it acts like a ground plane.
[Altium's documentation](https://www.altium.com/documentation/altium-designer/pcb-layout-high-speed-design) says:

> The width of the return path is ideally 3x the width of the signal routing, or 3x the distance from the route to the plane, whichever is smaller. While the greatest current density is directly below the signal route, it also spreads out into the plane on either side of the route with approximately 95% flowing within 3x the route width.

Here's what this would look like:

{{< figure caption="Demo of what transmission line routing could look like, with a ground trace (green) automatically routed underneath the signal trace (red)." src="/img/transmission-lines/kicad_transline_routing.gif" >}}

In most cases, you'd probably still want a ground plane, so this extra trace might seem redundant.
(And that's true - if you have a ground plane, the current return trace will likely not change the copper at all, since the ground plane would cover the same area.)

The return trace essentially acts as a way of getting the [DRC](https://en.wikipedia.org/wiki/Design_rule_checking) engine to enforce best practices for your current return path.
While routing, DRC would consider obstructions on both layers, and prevent you from routing your transmission line too close to holes/vias, traces belonging to other nets, etc.
After you've routed your high-speed signals, the return trace would essentially act as a keep-out zone within the plane, preventing traces and vias for other nets from intruding into this sensitive area.

This functionality could also make constructing your return path faster: if you add a via to move your signal trace to the other side of the board, it could automatically create a via for the return path as well.
The software could find the best placement for the ground via given the obstructions nearby (e.g. placing the ground via on the left or right side of the trace, forward or behind the signal via.)
It could also omit the ground via if there's already one sufficiently close by.

{{< figure caption="Example of how it might automatically place a ground via next to a signal via." src="/img/transmission-lines/auto_ground_vias.png" >}}

If you draw all your transmission lines before adding ground planes, the ratsnest lines can help remind you where you need to connect the IC ground/power pins to the current return path, helping you avoid accidentally creating a large loop.

{{< figure caption="Ratsnest lines (faint white line) between IC ground pins and the current return path, showing you the connection that needs to be made." src="/img/transmission-lines/ratsnest.png" >}}

## Differential pairs

Of course, the same idea can be applied to differential pairs as well (since they're typically controlled-impedance transmission lines).
The current return path would be one wide trace underneath both of the signal traces (or two overlapping traces, one underneath each of the signal traces; this might handle corners slightly better.)
So instead of routing 2 traces simultaneously, we'd route 3-4 traces.
Any time you add vias, it would add 3 or 4 vias (two for the signal traces, 1-2 for the return current).

{{<
    figure caption="Example showing how it might place ground vias for differential pairs."
    src="/img/transmission-lines/ground_vias_diff_pair.png"
    >}}

# Further improvements

With more features, this functionality could be more flexible:

## Automatic stitching capacitors

Perhaps the tool could detect which net the inner layer zone is connected to, and automatically create stitching capacitors when you cross splits or switch sides:

{{< figure caption="Example showing a stitching capacitor automatically added when crossing a zone split."  src="/img/transmission-lines/multi_zone_stitching.png" >}}
{{< figure caption="Example showing a stitching capacitor automatically added when changing sides with two planes connected to different nets." src="/img/transmission-lines/two_side_stitching.png" >}}

## Other transmission line topologies

Of course, microstrip isn't the only transmission line topology possible on a PCB.
This idea could be extended to [stripline](https://en.wikipedia.org/wiki/Stripline), [coplanar waveguides](https://en.wikipedia.org/wiki/Coplanar_waveguide), or [other types of transmission lines](https://resources.pcb.cadence.com/blog/2022-types-of-transmission-lines-in-high-speed-pcb-layout).

## Smarter ratsnest

Currently, KiCad's strategy for ratsnest lines (the thin white lines that indicate disconnected areas belonging to the same net) is to draw a line to the nearest pad or corner of a zone or trace belonging to that net.
If KiCad is aware that the wide inner-layer trace is meant to be a current return path, it could be smarter about where to draw this line to.
Instead of picking any random `GND` (or whichever net it belongs to) copper nearby, it should:

 - Find where the end of the signal trace needs to go
 - Find the pin that:
    - belongs to the same component as the signal destination pin
    - belongs to the correct net (e.g. `GND`)
    - is closest to the destination pin.

Then it should draw the ratsnest line from the end of the current return trace to the pin it found.

## Automatic return current vias

Once we have the ability to automatically choose which pin the return path should connect to, why not go a step further and automatically connect it?

Similar to how the differential pair routing mode automatically makes a connection to both the `+` and `-` pads on each end, we could automatically create a trace and via from the ground or power pin nearest the signal pin. In a lot of the previous examples, I've left the inner-layer trace unconnected at each ends, but it should be possible to do some basic automatic routing for these connections.

## Being explicit about current return nets

It might make sense to have the user be explicit about which net they want to use for the current return path.
I can imagine a few ways to accomplish that:

 - A label naming convention / suffix, analogous to how differential pairs currently work in KiCad. Something like `<signal name>_RET` or `<signal>_RETURN` perhaps. This would lead to your `GND` and various power nets having a bunch of extra labels attached.
 - A new type of connection in the schematic editor representing a transmission line; this would encapsulate two (or three for diff pairs) nets.

{{< figure caption="Mockup of what a transmission line could look like in the schematic editor. In this example, ground is used as the return current net."  src="/img/transmission-lines/eeschema_transline_mockup.png" >}}

The latter might be harder to implement but would be more flexible.
For example, it would allow the user to explicitly model stitching capacitors:

{{< figure caption="Schematic editor transmission line mockup with capacitors to allow for signal to flow between two different power nets." src="/img/transmission-lines/eeschema_transline_mockup_caps.png" >}}


# What do you think?

Please let me know what you think of this idea.
Would you find it helpful?
Do you have suggestions on how to make it better?

`TODO: feedback channels`
