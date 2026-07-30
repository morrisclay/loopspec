---
set: held_out
domain: factory
encoded_by: gemini-2.5-pro
written_without_ontology: true
---

# Flex-Tech Assemblies, Plant 2

The day at Flex-Tech starts at 7:00 AM with the production stand-up. Dave, the Plant Manager, stands with Maria, the line supervisor for the Veridian account, and Ken, the Quality Lead. The whiteboard behind them shows yesterday's numbers for the V-78b Power Control Module line: 7,850 units shipped against a target of 8,000. First Pass Yield (FPY) was 96%, a point below the 97% goal. Downtime was 45 minutes, logged against "Station 4, component jam."

Veridian Dynamics is their biggest customer. Flex-Tech builds the power modules to Veridian's exact design package—the Gerber files for the PCB, the CAD for the plastic enclosure, the bill of materials (BOM), and the approved vendor list (AVL). Flex-Tech’s margin on each $12 module is about sixty cents, and that’s only if everything goes perfectly.

The "component jam" at Station 4 is the main topic. Station 4 is where the populated PCB is snapped into the bottom half of the injection-molded enclosure. Maria explains, "It's the new batch of housings from PolyPlast. The retaining clips are stiff. The operators have to apply extra pressure, and sometimes the board doesn't seat right. It’s slowing them down and causing the board to misalign, which is why we're seeing more failures at the in-circuit test station down the line."

Dave looks at the pallet of new housings. He knows calling PolyPlast will just start a three-day argument about whose calipers are better calibrated. They can't afford to shut down the line. Veridian's final assembly plant in Mexico has no buffer; a missed shipment from Flex-Tech means their own lines go down, a catastrophic failure that comes with immense financial penalties and a black mark on Flex-Tech’s supplier scorecard.

"Can we make it work?" Dave asks. It's not really a question.

Maria nods. "I'll tell the guys to use the dead-blow hammers to seat them. Gently. We'll add a secondary visual check right after Station 4 to make sure the board is flush before it goes to the top-side assembly." This is the reality of contract manufacturing: sanctioned workarounds.

The line runs. On the SMT (Surface-Mount Technology) side, automated pick-and-place machines place hundreds of tiny resistors and capacitors onto bare boards at blinding speed. The boards then go through a reflow oven. This part is mostly automated. The real trouble is in the "back end," the manual assembly. Here, twenty operators stand at brightly lit stations, performing single, repetitive tasks: snapping in the board, attaching a wiring harness, sonic-welding the top enclosure, applying a serial number label. At the end, each unit goes into a test fixture—a "bed of nails"—for an In-Circuit Test (ICT) to check for shorts and open circuits, followed by a functional test that simulates operation. A green light means it goes in a box. A red light means it goes on the "bone pile" for the rework technician, an expensive detour.

### What people are trying to judge that they cannot see directly

Dave, the Plant Manager, is trying to gauge the *actual* inventory level at Veridian's Mexico plant. Their purchasing system says "zero buffer," but Dave has been doing this for twenty years. He suspects they keep a day or two of "dark inventory" off the books to protect themselves. His decision to push Maria for a workaround, rather than stopping the line to fight with the sub-supplier, is a bet on the existence of that unseen buffer. He’s judging his customer’s true fragility, not their stated one.

Maria, the line supervisor, is trying to judge her team's morale and ergonomic strain. The dashboards show Units Per Hour (UPH), but she is mentally tracking how many times an operator has to shake out their wrists, or the tension in their shoulders. Pushing them to use hammers to seat a part might hit today's target, but she knows it risks a repetitive strain injury tomorrow, or just a general burnout that will tank productivity for the rest of the week. She is judging the line's human capacity, a metric with no screen.

Ken, the Quality Lead, is trying to judge if the 4% failure rate is *stable*. He’s staring at the Pareto chart of failure codes from the test station. Most are "component alignment," which fits the stiff-enclosure theory. But he sees a small uptick in "U-17 checksum error." Is that just random noise, or is it a sign that the physical shock of hammering the boards in is causing latent damage to one of the microcontrollers? He's trying to predict future field failures from ambiguous present-day data.

### What makes it hard

The core difficulty is the split responsibility. Flex-Tech is responsible for the *process*, but Veridian is responsible for the *design*. When a problem like the stiff enclosures occurs, Flex-Tech sees it as a design-for-manufacturing (DFM) failure. The clip is too thick, the tolerance is too tight. They can submit an Engineering Change Request (ECR) to Veridian, but that process takes months of reviews and re-qualification. By then, the V-78b module will be at the end of its life. So they are forced into inefficient workarounds on a design they cannot change.

The margins make it harder. There is no money for slack. They can't afford to buy a hundred thousand extra enclosures to have a buffer. They can't afford a top-of-the-line force-monitoring press for Station 4 that would seat the board perfectly every time. They use people and hammers because they are cheaper and more adaptable than capital equipment they don't have the budget for.

Finally, the supply chain is a chain of blame. Flex-Tech gets squeezed by Veridian's demands, so they squeeze their own supplier, PolyPlast. PolyPlast, in turn, is probably dealing with inconsistent raw resin from their supplier. The problem cascades down, but the responsibility for hitting the final number always stops at Flex-Tech.

### Who bears the cost when it goes wrong

Immediately, Flex-Tech bears the cost. The units that fail testing on the line are reworked on Flex-Tech's dime. The operator's time, the rework technician's time, and the potential for scrapped components all come directly out of their sixty-cent margin. If Dave’s bet is wrong and a shipment is late, they pay the contractual penalty to Veridian.

In the medium term, Veridian bears a cost. The workaround—hammering the boards in—might be causing microscopic fractures in solder joints. These units pass the functional test at the plant. But six months later, in a hot kitchen, the thermal cycling causes the crack to propagate and the module fails. This becomes a field failure, and Veridian bears the warranty cost and the damage to its brand reputation.

Ultimately, the cost circles back to Flex-Tech. When Veridian's quarterly supplier review comes up, Flex-Tech's scorecard will show the late shipment and a higher-than-
