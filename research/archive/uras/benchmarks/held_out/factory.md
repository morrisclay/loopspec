---
set: held_out
domain: factory
encoded_by: gemini-2.5-pro
written_without_ontology: true
---

# The SW-77B Job at Apex Manufacturing

The process starts not with a bang, but with a PDF. An email from the buyer at Starkweather Industrial lands in the inbox of Maria, a planner at Apex Manufacturing in Dayton, Ohio. It’s a Purchase Order for 10,000 units of the SW-77B, a damper control housing assembly for a commercial HVAC unit. The PO specifies a price of $14.52 per unit and a delivery schedule of 1,250 units per week, starting in eight weeks.

Maria pulls up the Bill of Materials (BOM) for the SW-77B. It’s a familiar job. Apex stamps the main housing from 22-gauge galvanized steel, spot-welds a mounting bracket, and then sends it to an assembly cell. In assembly, operators install a small stepper motor (sourced from Globex Motors), a position sensor (from a distributor in Chicago), and a pre-made wiring harness.

Maria’s first action is to check material availability. The AS400 system shows they have enough steel coil on hand, but the Globex motors are a long-lead item. She issues a PO to Globex for 10,500 motors—the 10,000 for the job plus a 5% buffer for potential fallout. The system says Globex has a 6-week lead time. It will be tight.

Next, she releases a work order to the shop floor. Frank, the plant manager, sees it pop up in the production schedule. He knows the SW-77B needs 80 hours on the 400-ton Minster stamping press. He has to slot it in between a run of automotive brackets for Genodyne and a smaller job for a local appliance maker. He juggles the schedule, knowing the Genodyne buyer will scream if his shipment is even a day late.

On the floor, Dave, the die-setter, gets the work order. He spends three hours pulling the heavy die-set for the SW-77B from storage, loading it into the Minster press, and bolting it down. Then begins the delicate process of "dialing it in." He runs a single part, stops the press, and walks the "first article" over to the Quality lab. There, Sarah, the QC tech, puts it on the CMM (Coordinate Measuring Machine) and checks 15 different critical dimensions against the Starkweather engineering drawing. The first part is out of spec on a hole location by .010 inches. Dave goes back, shims the die, and runs another. This one is good. Sarah signs the First Article Inspection Report, and Dave gets the green light to start the production run. The press begins its rhythmic *ka-CHUNK, ka-CHUNK*, spitting out a raw housing every 12 seconds.

### What People are Trying to Judge

Maria, the planner, cannot see the actual production status at Globex Motors. Her supplier portal says the order is "In Process," but that could mean anything. She’s trying to judge the *real* probability of those motors arriving on time. Last time, a "quality hold" at Globex delayed a shipment by four days, forcing Apex to pay overtime on a weekend to catch up. She’s judging the trustworthiness of a single line of text on a web page.

Frank, the plant manager, is trying to judge the *true capacity* of his assembly line. The time-study says each SW-77B takes 4.5 minutes to assemble. But he knows that doesn't account for the new operator, Kevin, who is still fumbling with the torque wrench, or the fact that one of the pneumatic screwdrivers on the line has a slow leak that maintenance hasn’t gotten to yet. The system says he has capacity; his gut tells him he’s going to miss the weekly target by 50 units.

Sarah, in QC, is trying to judge process stability from a tiny sample. She’s required to pull five assemblies per hour and run them through a function test. If all five pass, the process is "good." But she knows a bad batch of sensors could have a 10% failure rate, and a sample of five could easily miss it. She’s judging the health of a thousand-piece lot from a five-piece snapshot.

### What Makes It Hard

**Margin:** Apex quoted this job at a 6% gross margin. That’s $0.87 per unit. If the stamping press goes down for an unscheduled four-hour repair, the cost of the idle labor and the technician's time completely erases the profit from the first week's shipment. There is no buffer for things to go wrong.

**Changes:** Starkweather is notorious for issuing Engineering Change Orders (ECOs) mid-production. Two months ago, on this same part, they decided to add a drain hole. The ECO came through on a Tuesday morning. Apex had to stop the press, pull the die, send it to the tool room to have the new feature machined in, and then go through the entire First Article Inspection process again. It cost them a day and a half of production, a delay for which they were not compensated.

**Upstream Brittleness:** The stepper motor from Globex is sole-sourced. Starkweather specified it on their drawing. If Globex has a fire, a strike, or a quality issue, Apex is completely stuck. They can’t substitute another motor without getting formal, written deviation approval from Starkweather’s engineering department, a process that can take weeks.

### Who Bears the Cost

If Dave sets the die improperly and produces 1,000 out-of-spec housings before it’s caught, **Apex eats the cost**. The steel is scrap, the press time is lost, and the labor is wasted. It shows up on Frank’s "Scrap, Rework, and Waste" report, and it comes directly out of the job’s margin.

If an assembly operator miswires a batch of 50 housings and they are shipped to Starkweather, the cost multiplies. The bad units cause Starkweather’s assembly line to go down. They will issue a formal Corrective Action Request (CAR). Apex will be "charged back" for Starkweather’s downtime. Apex will also have to pay, out of pocket, for a third-party sorting company to inspect every single SW-77B in Starkweather’s warehouse, at a cost of several dollars per unit. The failure will also tank Apex's score on Starkweather's quarterly supplier scorecard, jeopardizing their chance at the next big contract.

If Frank’s scheduling gamble fails and the Genodyne job is late because he prioritized the Starkweather run, **Apex pays the penalty**. Genodyne’s contract includes a $5,000 per day late fee.

### What Everyone Knows But Nobody Writes Down

The Starkweather drawing specifies a flatness tolerance of .005 inches on the main mounting surface. Everyone at Apex, from the press operator to the plant manager, knows that as long as it’s under .010, it works fine and Starkweather’s line will never notice. Chasing the "drawing spec" is a waste of time and money that increases the scrap rate.

When there's a quality problem, the first phone call determines the narrative. You never admit fault immediately. The initial response is always, "We're investigating a potential process variation and will get back to you." You buy time to figure out if you can blame the material, the spec, or the shipper.

The weekly production numbers reported in the Tuesday morning meeting are always based on what has been packed in the box. The 75 units sitting in the rework bin waiting for a replacement sensor don't count against the total until it's absolutely certain they can't be shipped by Friday.

The buyer at Starkweather is measured on cost reduction. Everyone knows that next year, he will come back and demand a 3% price reduction on the SW-77B, regardless of what happens to steel or labor costs. The current quote is just a temporary truce.

## What this should break
*   An assumption that the specifications of the product are static. A formal model would treat the engineering drawing as "truth," when in reality it is a starting point for negotiation and is subject to change mid-process via ECOs, creating moving goalposts.
*   An assumption that data from the system is a reliable reflection of reality. A model would ingest "line efficiency" or "supplier lead time" as hard numbers, when they are known by the participants to be gamed, buffered, or based on incomplete information.
*   An assumption that the cost of a failure is a known, quantifiable variable. A model would assign a fixed cost to a bad part, but the real cost is ambiguous, negotiated after the fact, and includes unquantifiable reputation damage that influences future contracts.
*   An assumption that agents make decisions to optimize a single, global utility function (like "minimize cost"). In reality, decisions are local and political; a planner expedites for the "loudest" customer, not the most profitable one, and an operator avoids a complex setup to make his own shift easier, pushing risk downstream.
*   An assumption that process steps are independent, linked only by inventory buffers. A model would miss that a "technically in-spec" but borderline part from the stamping press makes the assembly operator's job materially harder and slower, a human-to-human transfer of difficulty that is invisible to the system.
*   An assumption that the contract (the Purchase Order) defines the rules of engagement. A model would treat the PO as the system's constitution, but the unwritten rules—the "real" tolerances, the protocol for reporting bad news, the expected annual price-down—are the actual drivers of behavior.
