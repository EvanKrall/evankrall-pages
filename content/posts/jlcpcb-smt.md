---
title: "Designing a PCB in EasyEDA and getting it assembled by JLCPCB"
date: 2020-10-12T19:20:28-07:00
draft: false
---

Recently I designed a PCB and had it made and assembled by [JLCPCB](https://jlcpcb.com/).
This is the first time I've ever done anything like this -- I've designed circuits on paper, built them on breadboards, soldered circuits together on proto-board PCBs, but before this project I'd never used an EDA program, ordered PCBs, or gotten a board assembled by a manufacturer.
I figure it's worth writing up what I've learned.

As of the time of writing, I haven't received the assembled boards, so this isn't a review of JLCPCB's PCB or SMT services.
I went with JLCPCB / [EasyEDA](https://easyeda.com) because they integrate nicely together, and JLCPCB is cheap.

# Overview

If you have an idea for a circuit and want to get it manufactured, there are a few major steps:

1. Design your schematic.
2. Lay out your PCB.
3. Fill out your BOM (Bill of Materials).
4. Send the Gerber, BOM, and PNP files to JLCPCB for manufacture / assembly.

I found the BOM to be the trickiest part of this.
While JLCPCB and EasyEDA are partnered with (or possibly actually the same company as) LCSC, a component supplier with over 100k parts, JLCPCB's SMT service supports a much smaller subset.
I found that it's much easier to constantly consult [JLCPCB's parts page](https://jlcpcb.com/parts) while designing your schematic.
This helps you avoid surprises later on.

EasyEDA has [very detailed documentation](https://docs.easyeda.com/en/Introduction/Introduction-to-EasyEDA/index.html).
In this post I'm going to explain the basics and what is needed specifically to get SMT assembly from JLCPCB.

# Designing your schematic

To design a schematic in [EasyEDA Designer](https://easyeda.com/editor), you create a new project (`File` -> `New` -> `Project...`, then within that project you create a new schematic.

You can find components to place on the schematic in the EELib (for simple components like resistors, capacitors, LEDs, headers) or the Library (for all the components from LCSC, plus custom components defined by you or the community.)
You can then place wires by clicking Wire(W) in the Wiring Tools widget (top right by default.) or pressing the `W` key.
Ground can be found in the Wiring Tools or EELib.

If your circuit is complicated enough, you'll want to split it into multiple sheets.
Click the plus button next to the list of sheets on the bottom left of the schematic view.
To connect parts of your circuit from different sheets, add Net Ports from the Wiring Tools widget.
Two net ports with the same name are considered to be connected to each other.
This also has the side effect of naming that net -- net names are visible in the PCB editor later, which can be helpful.
(Otherwise, the default net names are things like `U1_38` -- the component and pin number of one of the components connected to the net.)

## Part selection for JLCPCB

If you're planning on having JLCPCB assemble your boards for you, then you'll want to stick to parts that JLCPCB can support.
All of the parts supported by JLCPCB are listed on their [parts page](https://jlcpcb.com/parts).
If there's a specific part they don't support, you can probably find that part in EasyEDA's Library and use it in your schematic / PCB design, but JLCPCB won't populate it for you -- you'll have to solder it yourself.
For these parts, you'll want to make sure you stick to parts you are capable of soldering yourself.
If you don't have the equipment to do SMT reflow at home, this probably means sticking to larger-pitch SMT or through-hole components.

### Basic vs Extended

There's a subset of JLCPCB's parts that they call *Basic* parts.
All other parts they support are called *Extended* parts.
Basic components have a cost per unit.
For each type of Extended component you use, JLCPCB adds $3 to your total cost.
If you aren't careful, this can really add up.
For example, if your board needs 10 different types of resistors, and you choose Extended components for these, then you'll end up paying $30 in fees on top of your per-component and assembly costs.

I found the best way to make sure I was choosing Basic parts was to use [JLCPCB's parts page](https://jlcpcb.com/parts) instead of trying to do it entirely through the Library.
In EasyEDA's Library pane, you can filter for `JLCPCB Assembled` components, and sort by the `SMT Type` column, but I found that this was sometimes out of sync with JLCPCB's parts database, so you may not find parts that JLCPCB actually has, or they may tell you something is Extended when it's actually Basic.
To avoid that, just go to the JLCPCB parts page and browse or search for what you're looking for, then filter for `Basic Parts`.


### Minimum order quantities

For most components, JLCPCB has a minimum order size.
**They don't tell you this until very late in the process:** once you've already submitted your Gerber/BOM/PNP files and are on the order review page.
If you use less than the minimum quantity, they charge you as if you had ordered the minimum quantity.
Many simple components, like resistors and capacitors, cost fractions of a cent, so this doesn't matter much.
However, for ICs it may matter more.
In my board, I used the [XL1509](https://jlcpcb.com/parts/componentSearch?searchTxt=C74192), which is LCSC part `C74192`.
JLCPCB's parts page shows you that this costs about 19 cents each, but does not tell you the order quantity.
This part ends up having a minimum order quantity of 10, so even though I only needed 5 (for an order of 5 boards), I'm paying for another 5 that I'm not going to use.

For small, cheap components like resistors and MLCC capacitors, it seems like generally the minimum quantity is 40.
For slightly less cheap components like diodes, inductors, tantalum capacitors, the minimum quantity is generally 20.
For ICs, the minimum quantity is probably 10.

In hindsight, I should have ordered 10 copies of my PCB instead of 5. This would have cost me $24+shipping instead of $22+shipping.
(20 would have cost me $33, 30 would have cost $38.)

# Laying out your PCB

Once you've designed your schematic, you need to turn it into a PCB layout.
In EasyEDA, go to `Design` > `Convert to PCB`.
This will create a PCB file within your project, and drop you into the PCB editor.

Enter the basic parameters of your board (board outline, dimensions, and copper layers -- you can edit these later if you need to.)
For me, the default position of the board outline (in purple) is way below (0, 0), so I changed the board outline with `Tools` > `Set Board Outline...`.

You'll see the PCB footprints of all your components, and a bunch of blue lines connecting pads.
These blue lines are called "ratlines", and these indicate which pads are supposed to be connected to each other.

Place your components where you want them to be, and then connect the pads with PCB tracks (under PCB tools, or hit `W`.)
(Or, run the auto router to wire up all the components for you.)

## Track width vs. current

In schematics, we pretend that wires have zero resistance. In the real world, copper has resistance depending on its cross-section and length.

Unless you're doing something high-speed or high-voltage, then the most important parameter dictating the width and length of the tracks on your PCB is current draw.

There are various PCB trace width calculators out there, such as [this one from 4pcb](https://www.4pcb.com/trace-width-calculator.html), which all seem to use the same formulas (IPC-2221).
These will tell you that an 0.254mm trace on the top or bottom layer of a PCB can handle about 885mA before they heat up more than 10 degrees C above ambient.
If your board is pretty small, and using less than that much current, you can probably leave the trace width in the Autorouter at the default 0.26mm.
However, a 0.254mm width trace of 57mm long carrying 885mA will drop about 100mV due to its resistance, so if you're using more than a few hundred milliamps you should probably try to keep your power traces short, wide, or use copper pours for higher current.

## Autorouter

If your board is more than a few components, you'll probably want to let a computer figure out how to lay out the PCB tracks.
Go to `Route` > `Auto Router...`, and hit `Run`.

If you're unlucky like me, you'll constantly get errors about cloud router server resources:

> Due to the limitation of router server resources, multiple routers executing concurrently are not supported, please try again later or do it manually :-)

If you see this, I recommend installing the [local auto-router](https://docs.easyeda.com/en/PCB/Route/index.html#Local-Auto-Router).
Usually, my board ended up taking between 10 and 30 seconds to route using the local auto router on my laptop.
(Faster than the cloud server, and not long enough to burn my lap.)

The auto-router is stochastic -- it won't give you the same results every time.
This can be helpful: if you don't like the way it's routed something, try running it again and see if you like it better.
However, it can also be annoying, especially once you've placed some copper pours and it decides to reroute GND to the other side of a chip.

You can define trace width or spacing requirements for certain nets under the Special Nets tab.

If you want the auto-router to only route things that need routing, you can check `Skip Routed Nets` under the `Skip Nets` tab.
However, this considers a net routed if there are _any traces belonging to that net_, which means if you've got the `GND` pin of two components wired together, it won't wire up _any other GND pins_.
This is quite annoying.

Sometimes, the auto-router may not be able to figure out a route for things.
Usually when this happens, it'll get stuck at almost-100% progress (you'll actually see the progress go back and forth as it tries various mutations), and then will time out after a while.
The `Information` dialog that pops up after the auto-router finishes will tell give you a non-zero number of `Failed` connections.
If this happens, take a look around the board to see what it's having trouble with.
Occasionally, you'll be able to see a solution to the problem, and you can manually finish wiring.
Other times, you'll need to move components around so that there's room for traces.

I spent a lot of time going back and forth moving components around and running the auto router.

## Changing your Schematic and updating your PCB.

If you need to make a change to your schematic after you've done a bunch of work in the PCB editor, don't worry.
You can edit your schematic, and then use `Design` > `Update PCB` to update your PCB file.
This will usually result in a pretty minimal disruption of your PCB.
New components will be placed somewhere outside the PCB boundary, and ratlines will be defined for any new connections.

# Filling out your BOM

If you used parts from EELib when designing your schematic, these won't have LCSC / JLCPCB part numbers associated with them.
You'll need to associate them with parts that JLCPCB knows about.
You can do this within EasyEDA or later, within the JLCPCB ordering flow.
If you only ever placed components on your schematic by referencing the LCSC part number from the JLCPCB parts page, then your BOM should already be complete.

## Parts you don't want JLCPCB to place

Some components in your circuit may not be available at JLCPCB, or you don't want them populated on the assembled boards for some reason.
For these parts, you can tell EasyEDA not to bother including them in the BOM by:

1. Within the Schematic (not the PCB view), right click on the component and click `Attributes...`.
2. For `Add to BOM`, select `No`.
3. Click `Update`.

(You can also leave them in your BOM, and tell JLCPCB not to place them while ordering.)

## Within EasyEDA

If you've got a bunch of components that need part numbers, you can do them quickly from the BOM view in EasyEDA.
From either the PCB or Schematic, go to `Fabrication` > `BOM...`.
This will show you a table of all the types of parts your circuit uses.
The column on the right, `LCSC Assembly`, supposedly tells you whether JLCPCB has that component in stock for SMT assembly.
I've found this frequently thinks a component is not available for assembly, even though I found it from the JLCPCB parts page.
**Always trust the JLCPCB parts page over anything you see in EasyEDA.**

- `Fabrication` > `BOM...`
- right click component > `Attributes...` >  `Supplier Part`

## Within JLCPCB order flow

Follow the instructions below for sending Gerber/BOM/PNP files to JLCPCB.
When you get to the part review phase, select your components.
More details are below.

# Sending the files to JLCPCB

## Downloading the files from EasyEDA

You'll need to export three files for JLCPCB to build and assemble your PCBs:

1. The Gerber file. This zip file describes the PCB itself -- where the boundaries, tracks, pads, through-holes, vias, etc. are on the PCB.
2. The BOM file. This is a CSV that tells JLCPCB what part number each component is.
3. The pick-and-place (aka PNP aka CPL) file. This is a CSV that tells the JLCPCB the location and orientation of each component on the board.

Download the Gerber file by going to `Fabrication` > `PCB Fabrication File (Gerber)`, or clicking the little folder icon with a G in it on the toolbar.
The Gerber file is only available when editing the PCB file.
It will ask you if you want to check DRC (Design Rule Checking) before generating the Gerber -- this is probably a good idea.
Click `Yes, Check DRC`.
If all goes well, it'll show you a preview of the board.
Click `Order at JLCPCB`, or `Generate Gerber`.
The former will send the Gerber file directly to JLCPCB, while the latter will download a zip file for you to upload to JLCPCB later.

Download the BOM file by going to `Fabrication` > `BOM...` or clicking the folder icon with a B in it on the toolbar.
Click `Export BOM`.
This will download a CSV file.
Unless you have components in your circuit that aren't available from JLCPCB, don't bother with `Order Parts / Check Stock`, which will take you an order page for LCSC.
For parts that JLCPCB has in stock, you don't need to buy these from LCSC, as they'll be included in your JLCPCB order.

Download the Pick and Place file by going to `Fabrication` > `Pick and Place file...` or clicking the folder icon with a little targeting icon in the toolbar.
This will open a dialog box.
Unless you're panelizing or having assembly done by somebody other than JLCPCB, leave the checkboxes unchecked.
Click `Export`.
This will download another CSV file.


## Ordering PCBs and SMT Assembly

### Upload the Gerber file

Go to [the order page](https://cart.jlcpcb.com/quote), or click "Quote Now" on the JLCPCB home page. (If you clicked `Order at JLCPCB` when generating the Gerber file, you can go to that tab and skip the next step.)
Click "Add your Gerber File" and select the zip file you downloaded.
Most of the important parameters should be populated after the Gerber file is uploaded.
Adjust the other options, such as quantity, but be aware that if you're ordering SMT service, you're pretty limited in your PCB options for some reason.
(Specific restrictions are listed on this order page or at their [marketing page for the SMT service](https://jlcpcb.com/smt-assembly).)
Only green PCBs :(

### Upload BOM and CPL (pick-and-place) files

Enable the switch next to `SMT Assembly`.
Choose whether you want the top or bottom side assembled by JLCPCB, and verify the quantity of boards.
If you're ordering 5 or 10 boards and enjoy soldering SMT components by hand, you can choose to have JLCPCB only solder 2 of boards for you.
I'm not sure if they ship you all the components they don't solder.

Click `Confirm`.
Sometimes this drops me back on the same page, and I have to scroll down and click Confirm again.

Click `Add BOM file` and select the BOM CSV.
It should be named `BOM_<project name>_<date>_<time>.csv`.

Click `Add CPL file` and select the pick-and-place file, which should be named `PickAndPlace_<PCB file name>_<date>_<time>.csv`.

Click `Next`.

### Verify your parts

You should see a table of all your BOM entries and what parts they are.
Double-check that JLCPCB knows about all the parts in your BOM.
If you want a part to be left off your board, you can uncheck `Confirmed`.
If a part number is missing, you can click the little magnifying glass icon in the `Matched Part Detail` column and search for a component.
This search interface is more limited than the [main parts search page](https://jlcpcb.com/parts), so you may want to cross-reference.
Check to make sure all the parts are `Basic Part`s, except for the ones you expect to be extended parts.

### Finish up

Click Next, review everything, and click Save to Cart.
If you want to change the number of PCBs, it's easier to do that after you've saved to cart than clicking `Go Back` all the way to the first page and redoing all the previous steps.

If you've gone through this flow multiple times (e.g. to correct an error) then you might have multiple PCB/SMT assembly items in your shopping cart.
Make sure you deselect or delete the ones you don't want to order, and then click `Checkout Securely`.

Fill out your billing and shipping addresses, and click `Continue`.

Choose your shipping method. For me, the two options shown by default were both about $16 or $17. If you aren't in a hurry, and want to save money, you can click `More` and it may show you a cheaper option. Unfortunately you'll have to select each of the options in turn to see how much they cost.

Click `Continue`, then `Submit Order`, then enter your payment info.

After you've placed your order, keep an eye out for emails from JLCPCB Support -- they wanted me to confirm the orientation of components such as diodes, capacitors, and ICs.

You've now made your order! Wait a few days, and maybe watch your [`Order history` page](https://jlcpcb.com/order) (log in, `Hi <username>` > `Order history`).
They will tell you what stage of production your PCB Prototype or SMT assembly is in.


In the mean time, maybe go write a blog post explaining what you learned.
