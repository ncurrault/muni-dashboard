import json
from collections import defaultdict
from pprint import pprint

with open(
    "../muni-dashboard2/all_10-06am.json",
    "r",
    encoding="utf-8-sig",
) as f:
    data = json.load(f)

with open("config.json", "r") as f:
    config = json.load(f)

with open("secrets.json", "r") as f:
    API_KEY = json.load(f)["apiKey"]

# stopRef -> list of expected departure times
upcoming_departures: defaultdict[str, set[str]] = defaultdict(set)

relevant_stops = set(stop["stopRef"] for stop in config)
stop_name_lookup = {}

for departure in data["ServiceDelivery"]["StopMonitoringDelivery"][
    "MonitoredStopVisit"
]:
    stop_ref = departure["MonitoredVehicleJourney"]["MonitoredCall"]["StopPointRef"]
    if stop_ref not in relevant_stops:
        continue

    if stop_ref not in stop_name_lookup:
        stop_name_lookup[stop_ref] = departure["MonitoredVehicleJourney"][
            "MonitoredCall"
        ]["StopPointName"]

    # check if line and direction is acceptable
    for option in config:
        if (
            departure["MonitoredVehicleJourney"]["LineRef"] == option["lineRef"]
            and departure["MonitoredVehicleJourney"]["DirectionRef"]
            == option["directionRef"]
        ):
            upcoming_departures[stop_ref].add(
                departure["MonitoredVehicleJourney"]["MonitoredCall"][
                    "ExpectedArrivalTime"
                ]
            )

upcoming_departures_sorted = {
    stop: sorted(departures) for stop, departures in upcoming_departures.items()
}

result = {
    "config": config,
    "stopNames": stop_name_lookup,
    "upcomingDepartures": upcoming_departures_sorted,
}

pprint(result)
