# ReliefMesh

A 2-day hackathon project. The goal is a **reliable working demo**, not a production system. See `Context.md` for the full background.

**Current focus: the backend logic only.** The frontend comes later, so for now everything should be testable without a UI.

## What we're building

An **offline AI dispatcher** that matches people's needs to nearby supplies when the internet and cell networks are down.

One laptop runs everything. People send requests in plain language, such as *"need 20L water, 4 of us at the library"*. The system works out what they need, finds the nearest place that has it, reserves the supplies, and messages both sides. The resource owner gets a dispatch order, and the requester gets a confirmation saying what's coming and from where.

## The core claim we must prove

**The AI and the coordination work with zero internet.** Use a locally running LLM, with nothing calling out to the cloud.

## Features

- A fixed set of about 8–12 locations, each a single point on the map (coordinates). There are no roads; distance is measured directly between two points
- Some locations hold supplies with quantities (water, food, medicine, insulin, blankets, power banks, baby formula)
- Simulated users: requesters, and resource owners linked to a location
- A requester is always at one of the known locations, and says which one in plain language ("we're by the bus depot")
- The AI turns a natural-language request into structured data (what, how much, where, how urgent), and asks one short follow-up if something is missing. For "where", it picks from the known location list, or answers "unknown" so the follow-up can list the options
- Matching finds the nearest location with enough stock and computes the distance and ETA (distance ÷ an assumed travel speed)
- Stock is reserved, and two short messages are written: one for the owner, one for the requester
- Each user has an inbox that these messages are delivered to
- The owner marks an order as sent, and the requester's inbox gets an "On the way" update
- When nothing is available, the requester gets a kind, useful fallback message
- A reset that restores a clean starting state

## Principles

- **Reliability beats features.** If something is flaky, cut it.
- **The AI handles language only:** understanding requests and writing messages. Matching, stock and distance are plain deterministic code, so the AI can never invent a resource.
- **Always validate AI output** against the known resource list and location list before using it.
- **Keep message delivery behind one pluggable layer.** It's an in-app inbox today, but it may later be phones over Wi-Fi or a Bluetooth mesh. The rest of the app shouldn't care which one is in use.
- Keep seed data in one place so the state can be reset instantly.
- Keep the pieces separate (intake, matching, dispatch, delivery) so teammates can work in parallel.
- Expose everything through an API so a frontend can plug in later.

## Scenarios that must work end to end

1. A requester asks for water. The right location is matched, stock drops, and the owner's inbox gets the order. The owner marks it as sent, and the requester's inbox shows "On the way".
2. A messy, urgent request ("my dad ran out of insulin, we're by the bus depot") is understood correctly and routed to the pharmacy.
3. The nearest location with a resource runs out, a new request for it comes in, and it is matched to the next-nearest location that still has stock.
4. A request for something that has run out gets a graceful fallback.