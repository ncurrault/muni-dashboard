import json
from collections import defaultdict
from pprint import pprint
import datetime
import requests
import os

USE_TEST_DATA = False
TEST_DATA_FILE = "../muni-dashboard2/all_10-06am.json"

CONFIG_FILE = "config.json"
TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


def get_config():
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)


def get_muni_data():
    if USE_TEST_DATA:
        with open(TEST_DATA_FILE, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
    else:
        API_KEY = os.getenv("API_KEY")
        response = requests.get(
            f"https://api.511.org/transit/StopMonitoring?api_key={API_KEY}&agency=SF&format=JSON"
        )
        # NOTE: 511 API supports filtering to a single `stop_code`, but we need
        # info on 3 stops at once, and the API rate limits to once per minute.
        # So here we request info on all stops in San Francisco (don't worry
        # about it) and filter it down locally

        if not response.ok:
            raise ValueError("511 API error")
        data = json.loads(response.content.decode(encoding="utf-8-sig"))
    return data


def is_departure_feasible(departure_timestamp: str, walking_time_secs: float):
    departure_datetime = datetime.datetime.strptime(
        departure_timestamp, TIMESTAMP_FORMAT
    )
    now = (
        datetime.datetime(2023, 6, 27, 17, 4, 17)
        if USE_TEST_DATA
        else datetime.datetime.utcnow()
    )
    station_arrival = now + datetime.timedelta(seconds=walking_time_secs)

    return station_arrival < departure_datetime


def construct_response_data(config, muni_data):
    # stopRef -> list of expected departure times
    upcoming_departures: defaultdict[str, set[str]] = defaultdict(set)
    relevant_stops = set(stop["stopRef"] for stop in config["options"])

    for departure in muni_data["ServiceDelivery"]["StopMonitoringDelivery"][
        "MonitoredStopVisit"
    ]:
        stop_ref = departure["MonitoredVehicleJourney"]["MonitoredCall"]["StopPointRef"]
        if stop_ref not in relevant_stops:
            continue

        # check if line and direction is acceptable
        for option in config["options"]:
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

    next_feasible_departures = {}
    walking_time_buffer = config.get("walkOptimizerBuffer", 0)

    for stop_ref in upcoming_departures_sorted.keys():
        walking_time = config["stopInfo"][stop_ref]["walkingTime"] + walking_time_buffer
        next_departure = next(
            (
                departure_timestamp
                for departure_timestamp in upcoming_departures_sorted.get(stop_ref, [])
                if is_departure_feasible(
                    departure_timestamp,
                    walking_time,
                )
            ),
            None,
        )
        if next_departure is not None:
            next_feasible_departures[stop_ref] = next_departure

    return {
        "upcomingDepartures": upcoming_departures_sorted,
        "nextFeasibleDepartures": sorted(
            next_feasible_departures.items(), key=lambda item: item[1]
        ),
    }


def get_result():
    config = get_config()
    muni_data = get_muni_data()
    result = {
        "config": config,
        "lastUpdated": datetime.datetime.now(datetime.timezone.utc).strftime(
            TIMESTAMP_FORMAT
        ),
        **construct_response_data(config, muni_data),
    }
    return result


# run this file directly to print the result
def main():
    res = get_result()
    pprint(res)
    with open("api_out.json", "w") as f:
        json.dump(res, f)


if __name__ == "__main__":
    main()
