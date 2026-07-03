# Watchman Completion Roadmap

Locked goal:
Watchman is an AI Weather Operations Center that answers weather decisions, explains reasoning, monitors change, and supports 1,000+ natural-language question types.

## Remaining intelligence domains

1. Weather Change Detection
2. Explain Your Reasoning
3. Confidence Intelligence
4. Sunrise/Sunset Intelligence
5. UV Intelligence
6. Astronomy Intelligence
7. Fire Weather Intelligence
8. Power Outage Risk
9. School Intelligence
10. Construction Intelligence Pro
11. Agriculture Intelligence
12. Photography Intelligence
13. Health Intelligence
14. Running and Exercise Intelligence
15. Camping Intelligence
16. Hunting Intelligence
17. Drone Flight Intelligence
18. Fishing Intelligence Pro
19. Emergency Management Intelligence
20. Personalized Preferences

Core rule:
Every Watchman answer should move toward this structure:
- answer
- verdict
- confidence
- evidence
- recommendation
- what would change the answer

## Astronomy Pro expansion

- Astronomy Pro: meteor showers, moon phase, planet visibility, eclipses, aurora, ISS passes, comets, constellations, and astrophotography conditions.

## Astronomy Pro Phase 2 (LOCKED)

Watchman Astronomy Pro will expand beyond weather-aware sky viewing into a complete astronomy intelligence engine.

Features to implement:

- Current moon phase
- Moon illumination %
- Moon age
- Next full moon
- Next new moon
- First quarter
- Last quarter
- Supermoons
- Blue moons
- Lunar eclipses
- Solar eclipses
- Planet visibility
- ISS passes
- Aurora forecasts
- Bright comet tracking
- Major constellation visibility
- Astrophotography conditions
- Moonlight impact on meteor showers
- Dark-sky recommendations
- Bortle-class integration (future)

Natural-language examples:

- When is the next full moon?
- Is there a full moon tonight?
- What phase is the moon?
- How bright is the moon tonight?
- When is the next new moon?
- When is the next supermoon?
- When is the next blue moon?
- When is the next lunar eclipse?
- When is the next solar eclipse?
- Can I see Saturn tonight?
- Can I see Jupiter tonight?
- Is the ISS flying over me?
- Will there be an aurora tonight?
- Can I see the Milky Way tonight?
- What constellations are visible tonight?
- Is tonight good for astrophotography?
- Will moonlight ruin the meteor shower?


## Solar Times expansion

- Solar Times Intelligence: exact sunrise, sunset, daylight length, civil twilight, nautical twilight, astronomical twilight, and solar noon.

## Watchman Decision Intelligence Module

Implemented target:
- Should I questions
- Can I questions
- Best time / worst time decisions
- Travel, outdoor, construction, sports, pets, home, event, and emergency decisions
- Verdict, confidence, evidence, recommendation, best time, worst time, and what would change the answer

## Astronomy Implementation Update

Implemented:
- Real Moon Phase Intelligence V1
- Next full moon / next new moon approximations
- Moon illumination and moon age
- Meteor shower moonlight impact
- Twilight Intelligence V1
- Civil twilight
- Nautical twilight
- Astronomical twilight
- Golden hour and blue hour approximation
- Solar noon approximation

## Watchman Identity Intelligence

Implemented:
- Watchman self-identity
- Brandon Douglas Chappell developer attribution
- Meteorologist limitation response
- Trust and confidence explanation
- Weather data explanation
- Capability explanation
- Emergency warning disclaimer

## Watchman Multi-Module Reasoning

Implemented:
- Combines multiple intelligence modules into one recommendation
- Uses Decision Intelligence as the primary verdict layer
- Pulls supporting evidence from hazards, lightning, travel, outdoor work, event, pet/livestock, marine/lake, moon phase, twilight, and solar time modules
- Returns verdict, confidence, modules used, combined score, evidence, and what would change the answer

## Watchman Intelligence Trio

Implemented:
- Reasoning Tree
- Conversation Memory
- Confidence Engine V2

Purpose:
Watchman now evaluates evidence branches, remembers recent exchanges by location, and can explain confidence with a score breakdown.

## Watchman Intelligence Core V2

Implemented:
- Reasoning Engine V2
- Timeline Intelligence
- Scenario Simulator

Purpose:
Watchman can now weigh evidence, detect conflicting signals, evaluate future time windows, and compare alternate scenarios.

## Watchman Next Intelligence Layer

Implemented:
- Decision Engine V3
- Route Intelligence V1
- Continuous Watch Mode V1

Notes:
Decision Engine V3 compares reasoning, timeline, and scenarios.
Route Intelligence V1 reads route intent and evaluates destination-weather risk; full corridor sampling is future work.
Continuous Watch Mode V1 stores an in-memory baseline for the current server session.

## Watchman Radar Intelligence V2

Implemented:
- Storm signal scoring
- Alert-aware radar risk
- Forecast-wording radar proxy
- Hourly storm arrival estimate
- Radar/storm recommendation

Note:
This V2 uses Watchman storm intelligence, alerts, and forecast timing. Live radar motion-vector ingestion is future work.

## Watchman Emergency Mode

Implemented:
- Tornado warning / tornado emergency detection
- Flash flood warning / emergency detection
- Destructive severe thunderstorm detection
- Extreme wind, hurricane, blizzard, winter storm, and excessive heat warning handling
- Emergency override above normal decision/radar/route answers
- Hazard-specific protective instructions
- Official guidance priority rule

## Watchman Notification Engine V1

Implemented:
- In-memory notification store
- Notification summary
- Unread notification support
- Notification API endpoint
- Mark-all-read endpoint
- Emergency/radar/alert/threat notification evaluation

Notes:
This is server-session notification infrastructure. Phone push, SMS, email, and PWA notifications are future delivery layers.

## Watchman Notification Engine V2

Implemented:
- Duplicate notification suppression
- Per-place notification signatures
- Alert/threat/radar/emergency change detection
- No repeated notification spam when conditions have not changed

Notes:
V2 keeps notifications meaningful by only creating a new notification when the tracked state changes.

## Watchman Notification Delivery V1

Implemented:
- Delivery outbox
- Phone-push pending channel
- Delivery API endpoint
- Notification-to-delivery queue bridge

Next:
- Android native notification bridge
- PWA service worker push
- Firebase Cloud Messaging or local Android WebView notification hook

## Watchman Phone Push Bridge V1

Implemented:
- Pending phone push endpoint
- Push acknowledgement endpoint
- Urgent pending summary
- Bridge between delivery outbox and future Android/PWA notification layer

Endpoints:
- /api/watchman/phone/push/pending
- /api/watchman/phone/push/ack
