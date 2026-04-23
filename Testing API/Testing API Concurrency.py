#Python Script to Test if the API works as expected
import requests              # used to send HTTP requests to your API
import threading             # used to simulate multiple users at once
import random                # used to generate random seat/event combinations
import time                  # optional: used for delays (can simulate real users)

#url to call the server the api is running on
#Change to an appropriate endpoint
BASE_URL = "http://ip-address-server-running-on:8000/api"

#Total number of simulated users
NUM_USERS = 100

#track results
success_count = 0
failure_count = 0

#Lock for safely updating shared counters across threads
#A lock ensures only one thread at a time can safely access or update shared data
#Shared data is just some variable threads are using at the same time.
lock = threading.Lock()


def simulate_user(user_id):
    """
    Simulates one user:
    1. Attempts to reserve a seat
    2. Attempts to purchase the same seat
    """

    #use the variables from outside this function
    #refers to the variables outside this function
    global success_count, failure_count

    try:
        #Generate random test data
        #This creates collisions (multiple users picking same seats/events)
        seat_code = f"A{random.randint(1, 50)}"
        event_id = random.randint(1, 20)
        expires_at = "2030-04-21 20:45:00"

        #Reserve seat
        reserve_response = requests.post(
            f"{BASE_URL}/reservations-class/",
            json={
                "user_id": user_id,
                "event_id": event_id,
                "seat_code": seat_code,
                "expires_at": expires_at
            }
        )

        # If reservation fails, stop this user
        if reserve_response.status_code != 201:
          #with lock means temporarily take the lock, run this block safely, then release it automatically.
          #Only one thread at a time can update failure_count
          #Prevents two threads from messing up the count
            with lock:
                failure_count += 1
            print(f"[FAIL] User {user_id} could not reserve {seat_code}")
            return

        #simulate user delay before payment
        time.sleep(random.uniform(0.1, 0.5))

        #STEP 2 Purchase ticket
        purchase_response = requests.post(
            f"{BASE_URL}/tickets/",
            json={
                "user_id": user_id,
                "event_id": event_id,
                "seat_code": seat_code,
                "price": round(random.uniform(10, 200), 2)
            }
                
        )

        #Evaluate purchase result
        if purchase_response.status_code == 201:
          #with lock means temporarily take the lock, run this block safely, then release it automatically.
          #Only one thread at a time can update success_count
          #Prevents two threads from messing up the count
            with lock:
                success_count += 1
            print(f"User {user_id} bought {seat_code} (event {event_id})")
        else:
            with lock:
                failure_count += 1
            print(f"User {user_id} purchase failed for {seat_code}")

    #Error Handling
    except Exception as e:
        with lock:
            failure_count += 1
        print(f"Error: User {user_id}: {e}")


def run_simulation():
    #Creates threads to simulate many users hitting the API at once
    threads = []

    #Create and start threads
    for user_id in range(1, NUM_USERS + 1):
        t = threading.Thread(target=simulate_user, args=(user_id,))
        threads.append(t)
        t.start()

    #Wait for all threads to finish
    for t in threads:
        t.join()

    #Final results
    print("\nSimulation Complete")
    print(f"Successful purchases: {success_count}")
    print(f"Failures: {failure_count}")


if __name__ == "__main__":
    run_simulation()