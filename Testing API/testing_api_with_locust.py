"""
What is Locust?
  Locust is a load testing tool. It pretends to be hundreds or thousands of users
  all hitting your API at the same time, so you can see how your server handles pressure.

How to install:
  pip install locust

How to run:
  locust -f testing_api_with_locust.py --host=http://127.0.0.1:8000

After running, open your browser at:
  http://localhost:8089
  

Recommended test stages (run one at a time, observe, then increase):
  Stage 1 — Warm up:    50 users,  spawn rate 10/s   ← baseline, should be fast
  Stage 2 — Pressure:  200 users,  spawn rate 50/s   ← normal load
  Stage 3 — Spike:     500 users,  spawn rate 100/s  ← heavy load
  Stage 4 — Break:    1000 users,  spawn rate 200/s  ← find the breaking point

What to watch in the Locust UI:
  RPS          → requests per second (throughput — higher is better)
  Median       → half of requests are faster than this (aim < 200ms)
  P95          → 95% of requests are faster than this (aim < 500ms)
  Failures %   → should stay near 0% for 500 errors (400s from collisions are normal)
"""

#IMPORTS

import random   # used to pick random seat codes, event IDs, prices, and user IDs
import time     # used to measure how long each request takes in milliseconds
import logging  # used to print warning messages when requests are too slow

# HttpUser  - the base class for a simulated user that makes HTTP requests
# task      - decorator that marks a method as something a user will DO
# between   - sets a random wait time between tasks (simulates real human think time)
# events    - lets you hook into Locust lifecycle events (like test stop)
from locust import HttpUser, task, between, events


#CONFIGURATION
#These numbers control the test data. Adjust them to match what's in your database.
#Highest user ID in your database; Locust picks random IDs between 1 and this
MAX_USER_ID = 800

#Highest event ID in your database; ocust will pick random IDs between 1 and this
MAX_EVENT_ID = 30

#The pool of seat codes Locust will randomly pick from.
#Keeping this small (A1–A19) intentionally causes collisions between users
#trying to book the same seat, test conflict handling logic in the API and database
#Example output: ["A1", "A2", "A3", ... "A19"]
SEAT_POOL = [f"A{i}" for i in range(1, 20)]

#Price range for ticket purchases; a random float between these will be used
MIN_PRICE = 10.0
MAX_PRICE = 200.0


#METRICS TRACKING
#Locust tracks HTTP-level metrics (status codes, response times) automatically.
#But we also want to track BUSINESS-LEVEL outcomes — did the booking actually work?
#This dictionary keeps those counts. Each key is a specific outcome we care about.

metrics = {
    "reservations_created":  0,  # POST /reservations-class/ returned 201; success
    "reservations_failed":   0,  # POST /reservations/ returned unexpected error
    "seat_collisions":       0,  # 400: seat already taken; expected under load, not a bug
    "tickets_created":       0,  # POST /tickets/ returned 201; success
    "tickets_failed":        0,  # POST /tickets/ returned unexpected error
    "no_reservation_errors": 0,  # 400: tried to buy without a valid reservation
    "server_errors":         0,  # 500: unexpected server crash; these should NEVER happen
}


def record(key: str):
    """
    Helper function to increment a metric by 1.
    Instead of writing metrics["reservations_created"] += 1 every time,
    we just call record("reservations_created").
    """
    metrics[key] += 1


#PRINT SUMMARY WHEN TEST ENDS
# @events.test_stop.add_listener tells Locust: "when the test stops, call this function"
# This gives us a final business-level report in the terminal after each test run.

@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    # Print a formatted summary of all business metrics to the terminal
    #separator line
    print("\n" + "=" * 55)
    print("  BUSINESS METRICS SUMMARY")

    #separator line
    print("=" * 55)
    print(f"  Reservations created:       {metrics['reservations_created']}")
    print(f"  Reservation failures:       {metrics['reservations_failed']}")
    print(f"  Seat collisions (expected): {metrics['seat_collisions']}")
    print(f"  Tickets created:            {metrics['tickets_created']}")
    print(f"  Ticket failures:            {metrics['tickets_failed']}")
    print(f"  No-reservation errors:      {metrics['no_reservation_errors']}")
    print(f"  Server errors (500s):       {metrics['server_errors']} should always be 0")
    #separator line
    print("=" * 55)

    # Calculate what % of reservation attempts ended in a seat collision
    # This tells you how "contested" the seat pool is under load
    total = metrics["reservations_created"] + metrics["reservations_failed"] + metrics["seat_collisions"]
    if total > 0:
        collision_rate = (metrics["seat_collisions"] / total) * 100
        print(f"  Collision rate:             {collision_rate:.1f}%")

    print("=" * 55 + "\n")


# ─── SIMULATED USER ───────────────────────────────────────────────────────────
# HttpUser is the base class for a simulated user.
# Everything inside this class defines what ONE user does while the test is running.
# Locust will create as many copies of this user as you set in the UI.

class BookingUser(HttpUser):
    """
    Simulates a real user going through the booking flow:
      1. Try to reserve a seat
      2. Wait a moment (like a real human would before paying)
      3. Purchase the reserved seat

    Locust runs each @task method repeatedly for every simulated user.
    The weight number on @task controls how often that task is chosen.
    Example: @task(3) means it's picked 3x more often than @task(1)
    """

    # wait_time controls how long each user waits between tasks.
    # between(0.5, 2) means each user waits a random 0.5 to 2 seconds between actions.
    # This simulates real human behaviour — people don't click instantly back-to-back.
    # Lower values = more aggressive load. Try between(0.1, 0.5) for extreme pressure.
    wait_time = between(0.5, 2)

    def on_start(self):
        """
        on_start() is called once when each simulated user first starts.
        Think of it as the user "logging in" or setting up their session.
        
        Here we assign each user a random user_id from your database,
        and set current_reservation to None (they haven't reserved anything yet).
        """
        # Pick a random user ID — this simulates different users making requests
        self.user_id = random.randint(1, MAX_USER_ID)

        # This will hold the seat/event data after a successful reservation,
        # so the purchase task knows what to buy. None means no active reservation.
        self.current_reservation = None

    # ── TASK 1: Reserve a seat ────────────────────────────────────────────────
    # weight=3 means this task is picked 3x more often than tasks with weight=1
    # This reflects real usage: users browse and attempt reservations more than purchases
    @task(3)
    def reserve_seat(self):
        """
        Simulates a user trying to grab a seat.
        Randomly picks a seat and event — collisions are intentional
        to test your unique constraint and conflict handling.
        """

        # Pick a random seat code from the pool (e.g. "A7")
        seat_code = random.choice(SEAT_POOL)

        # Pick a random event ID (e.g. 3)
        event_id = random.randint(1, MAX_EVENT_ID)

        # Record the time before the request so we can measure response time
        start = time.time()

        # self.client is Locust's built-in HTTP session — like requests.Session()
        # catch_response=True means we manually decide if the response is a pass or fail
        # without catch_response, Locust auto-fails anything that isn't 2xx
        # name= groups all reservation requests together in the Locust UI stats table
        with self.client.post(
            "/api/reservations-class/",
            json={
                "user_id":   self.user_id,  # integer — the user making the reservation
                "event_id":  event_id,      # integer — which event they want
                "seat_code": seat_code,     # string  — which seat they want
                "expires_at": "2026-07-20 10:00:00",
            },
            catch_response=True,
            name="POST /api/reservations-class/",
        ) as response:

            # Calculate how long the request took in milliseconds
            # time.time() returns seconds, multiply by 1000 to get milliseconds
            duration = (time.time() - start) * 1000

            if response.status_code == 201:
                # 201 Created — reservation was successfully made
                record("reservations_created")

                # Save the seat and event so the purchase task can use them later
                # Without this, the purchase task has nothing to buy
                self.current_reservation = {
                    "seat_code": seat_code,
                    "event_id":  event_id,
                }

                # Tell Locust this request counted as a success in the stats
                response.success()

            elif response.status_code == 400:
                # 400 Bad Request — could be a collision or a validation error
                # response.content checks the body isn't empty before parsing
                body = response.json() if response.content else {}

                # .get("error", "") safely reads the error key — returns "" if missing
                error = body.get("error", "")

                if "Seat Not Available" in error:
                    # This is EXPECTED — two users tried to book the same seat
                    # We mark it as success so Locust doesn't count it as a failure
                    # It's not a bug, it's your system working correctly
                    record("seat_collisions")
                    response.success()
                else:
                    # Something else went wrong — unexpected 400
                    record("reservations_failed")
                    response.failure(f"Unexpected 400: {error}")

            elif response.status_code >= 500:
                # 500 = server crash — this should NEVER happen
                # If you see these, your code has an unhandled exception somewhere
                record("server_errors")
                response.failure(f"500 server error: {response.text}")

            else:
                # Anything else unexpected (301, 403, etc.)
                record("reservations_failed")
                response.failure(f"Unexpected status: {response.status_code}")

            # If the request took more than 1 second, log a warning in the terminal
            # This helps you spot which endpoints are slowing down under load
            if duration > 1000:
                logging.warning(
                    f"SLOW reserve: {duration:.0f}ms — user={self.user_id} seat={seat_code}"
                )

    # ── TASK 2: Purchase a ticket ─────────────────────────────────────────────
    # weight=1 means this runs less often than reserve_seat (weight=3)
    # Reflects real usage: not every reservation leads to an immediate purchase
    @task(1)
    def purchase_ticket(self):
        """
        Simulates a user purchasing a ticket for their reserved seat.
        Only runs if the user has an active reservation from task 1.
        """

        # If this user hasn't reserved a seat yet, skip this task entirely
        # return exits the function immediately — nothing happens this cycle
        if not self.current_reservation:
            return

        # Grab the reservation data and immediately clear it
        # We clear it BEFORE the request so that even if the purchase fails,
        # the user doesn't keep trying to buy the same (now invalid) reservation
        reservation = self.current_reservation
        self.current_reservation = None

        # Record start time to measure response duration
        start = time.time()

        with self.client.post(
            "/api/tickets/",
            json={
                "user_id":   self.user_id,                                    # who is buying
                "event_id":  reservation["event_id"],                         # which event
                "seat_code": reservation["seat_code"],                        # which seat
                "price":     round(random.uniform(MIN_PRICE, MAX_PRICE), 2),  # random price
            },
            catch_response=True,
            name="POST /api/tickets/",
        ) as response:

            # How long did the purchase take in milliseconds?
            duration = (time.time() - start) * 1000

            if response.status_code == 201:
                # 201 Created — ticket successfully purchased and reservation deleted
                record("tickets_created")
                response.success()

            elif response.status_code == 400:
                body = response.json() if response.content else {}
                error = body.get("error", "")

                if "No valid reservation" in error:
                    # This happens when the reservation expired or was already used
                    # Under high load this is expected — not a server bug
                    record("no_reservation_errors")
                    response.success()  # mark as success — it's expected behaviour

                elif "Seat Not Available" in error:
                    # Seat was already purchased by someone else — expected collision
                    record("seat_collisions")
                    response.success()

                else:
                    # Unexpected 400 — something is wrong with the request itself
                    record("tickets_failed")
                    response.failure(f"Unexpected 400: {error}")

            elif response.status_code >= 500:
                # Server crash — should never happen, investigate immediately
                record("server_errors")
                response.failure(f"500 server error: {response.text}")

            else:
                record("tickets_failed")
                response.failure(f"Unexpected status: {response.status_code}")

            # Warn if the purchase took more than 1 second
            if duration > 1000:
                logging.warning(
                    f"SLOW purchase: {duration:.0f}ms — user={self.user_id} seat={reservation['seat_code']}"
                )

    # ── TASK 3: List all reservations (read load) ─────────────────────────────
    # weight=1 — runs occasionally to simulate users checking available seats
    # GET requests are much cheaper than POST, but under high load they still add up
    @task(1)
    def list_reservations(self):
        """
        Simulates a user fetching the list of all reservations.
        This is a read-only GET request — tests how fast your DB handles reads under load.
        """
        with self.client.get(
            "/api/reservations/",
            catch_response=True,
            name="GET /api/reservations/",
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                # Any non-200 on a simple GET is unexpected — flag it
                response.failure(f"GET reservations failed: {response.status_code}")

    # ── TASK 4: List all tickets (read load) ──────────────────────────────────
    # weight=1 — runs occasionally to simulate users checking purchased tickets
    @task(1)
    def list_tickets(self):
        """
        Simulates a user fetching the list of all tickets.
        Another read-only GET — tests read performance under write-heavy concurrent load.
        """
        with self.client.get(
            "/api/tickets/",
            catch_response=True,
            name="GET /api/tickets/",
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"GET tickets failed: {response.status_code}")