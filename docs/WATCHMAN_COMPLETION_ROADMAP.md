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

## Watchman Browser Phone Push V1

Implemented:
- Browser notification polling loop
- Polls /api/watchman/phone/push/pending
- Shows native browser notifications when permission is granted
- Acknowledges delivered pushes through /api/watchman/phone/push/ack
- Loads from static/watchman_phone_push.js

Notes:
This is browser/WebView notification delivery. Android native background push and Firebase Cloud Messaging are future layers.

## Watchman Android Notification Bridge V1

Implemented:
- Termux Android notification bridge
- Automatic Android notification attempt after Watchman creates delivery items
- Android bridge status endpoint
- Manual send-pending endpoint

Endpoints:
- /api/watchman/android/notifications/status
- /api/watchman/android/notifications/send-pending

Requirement:
- Termux:API app installed on Android
- termux-api package installed with: pkg install termux-api

Fallback:
If Termux notifications are not available, Watchman still keeps browser/WebView push polling and delivery outbox active.

## Watchman Android Notification Bridge V2

Implemented:
- Non-blocking Termux notification spawn
- Prevents Watchman request hangs when Termux:API stalls
- Tracks attempted Android notification IDs
- Tracks recent bridge results
- Keeps browser/WebView push fallback active

## Watchman Background Watch Loop V1

Implemented:
- Watch registry
- Register/unregister watched locations
- Manual run-once check
- Start/stop background loop
- Background checks trigger notification engine, delivery outbox, and Android bridge

Endpoints:
- /api/watchman/watch/register?place=Nashville
- /api/watchman/watch/list
- /api/watchman/watch/run-once
- /api/watchman/watch/start?interval=300
- /api/watchman/watch/stop

Notes:
This turns Watchman from ask-response into active monitoring while the Flask server is running.

## Watchman Persistent Watch Registry V1

Implemented:
- Saves watched locations to data/watchman_watches.json
- Loads watches on server start
- Preserves interval, enabled state, check count, and last status
- Saves after register, unregister, and background checks

## Watchman Auto-Start Watch Loop V1

Implemented:
- Loads persisted watches on server start
- Starts the background watch loop automatically when saved watches exist
- Keeps Watchman monitoring after server restart

## Watchman Alert ID Tracking V1

Implemented:
- Tracks seen official alert IDs/fallback signatures in memory
- Records alert history
- Adds alert tracking endpoint
- Prevents Walker County alert questions from being stolen by national-scope routing

Next:
- Wire alert tracking into notification dedupe so only new official alerts trigger alert notifications after restart.

## Watchman Storm Arrival Engine V1

Implemented:
- Estimates storm arrival from hourly forecast timing
- Uses Watchman storm signal, precipitation chance, and active alerts
- Answers storm timing / approaching / coming-from-east questions directly

## Watchman Change Detection Engine V1

Implemented:
- Tracks last scan by place in memory
- Detects alert count changes
- Detects threat score changes
- Detects precipitation changes
- Detects forecast wording changes
- Detects storm arrival estimate changes

## Watchman Alert Change Notification V1

Implemented:
- Tracks alert signatures by place
- Detects new alerts
- Detects cleared alerts
- Detects threat score changes
- Detects threat level changes
- Detects storm status changes
- Detects storm arrival changes
- Stores alert change results in background watch status

Next:
- Use alert_change.changed to suppress routine notifications unless state changed.

## Watchman Notification Suppression V1

Implemented:
- Suppresses routine alert/threat/radar notifications when alertChange.changed is false
- Allows emergency notifications to override suppression
- Keeps first-scan baseline behavior intact
- Reduces notification spam during steady conditions

## Watchman Radar Map Intelligence Overlay V1

Implemented:
- Adds /api/watchman/radar-map/intelligence
- Fetches official NWS alert polygon geometry
- Generates Watchman storm-cell proxy polygon from storm intelligence
- Converts existing radar iframe into Leaflet radar map
- Adds RainViewer radar tile layer
- Overlays NWS alert polygons and storm proxy polygon
- Adds polygon popups for alert/storm details

Notes:
Storm cell polygons are V1 proxy polygons based on Watchman intelligence. Live radar cell contour extraction is future work.

## Watchman NWS Alert Polygon Fallback V2

Implemented:
- Keeps official NWS polygon geometry when available
- Creates fallback alert polygons when NWS active alert geometry is missing
- Separates official polygons from fallback polygons in map counts
- Updates radar map label and map note wording

## Watchman Storm Movement Projection V1

Implemented:
- Estimates storm movement bearing from Watchman movement wording
- Estimates storm speed from movement wording or threat level fallback
- Adds projected storm polygons at +15, +30, and +60 minutes
- Adds dashed projection styling on the radar map
- Adds projection popup details: minutes, bearing, speed, movement

## Watchman Radar Motion Engine V1

Implemented:
- Adds /api/watchman/radar-motion
- Pulls RainViewer radar frame metadata
- Estimates bearing and speed from Watchman movement intelligence
- Generates 15/30/60 minute projection points
- Adds Radar Motion Engine panel below the radar map

Note:
This is motion intelligence V1. It does not yet extract pixel-level radar-cell contours from tile images.

## Watchman Radar Cell Tracker V1

Implemented:
- Adds /api/watchman/radar-cell-tracker
- Downloads recent RainViewer radar tiles around watched location
- Computes precipitation centroid from radar pixels
- Compares consecutive radar frames
- Estimates measured bearing, speed, movement distance, and confidence
- Adds Radar Cell Tracker panel to the radar map section

Notes:
This is the first real radar-frame tracking layer. It tracks the dominant precipitation centroid near the watched location, not yet multiple separated storm cells.

## Watchman Lightning Intelligence Layer V1

Implemented:
- Adds /api/watchman/lightning
- Creates lightning-risk score from storm/thunder signals, alerts, precip, radar motion, and radar cell tracking
- Adds lightning risk zone polygon
- Adds +15 and +30 minute projected lightning-risk zones
- Adds Lightning Intelligence Layer panel under the radar map
- Overlays lightning polygons on the existing Watchman radar map

Note:
This is lightning-risk intelligence, not a live lightning strike feed. Real strike-feed ingestion remains future work.

## Watchman Advanced NWS Polygon Layer V1

Implemented:
- Adds /api/watchman/nws-polygons/advanced
- Separates official and fallback polygons
- Classifies warning/watch/advisory/flood/statement/other layers
- Adds richer polygon styling
- Adds flashing warning borders
- Adds map layer controls for warnings, watches, advisories, flood, statements, and other
- Adds Advanced NWS Polygon Layer panel under the radar map

## Watchman Multi-Cell Storm Tracker V1

Implemented:
- Adds /api/watchman/radar-multi-cell
- Separates radar precipitation into rough multiple cells
- Tracks nearest matched cells between consecutive RainViewer frames
- Estimates per-cell bearing, speed, movement distance, confidence, and strength trend
- Adds Multi-Cell Storm Tracker panel to the radar map section

Next:
- Add split/merge detection
- Draw individual tracked cell IDs on the map
- Feed tracked cell motion into impact forecasting

## Watchman Impact Forecast V1

Implemented:
- Adds /api/watchman/impact-forecast
- Uses multi-cell radar tracks to project possible impact windows
- Creates 15/30/60 minute impact forecasts
- Calculates impact level, distance, confidence, speed, bearing, and recommendation
- Adds impact forecast zones to the radar map
- Adds Impact Forecast panel under the radar map

Next:
- Add town/road/route impact lookup
- Feed impact forecasts into Watchman decision engine
