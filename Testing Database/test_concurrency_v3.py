#Python script to test if the database works as expected
#simulates multiple users trying to book a seat
import psycopg2
import threading
import random

#function declaration
def book_seat(user_id):
  #connect to postgrsql
  conn = psycopg2.connect(
      dbname="event-booking-system",
      user="postgres",
      password="database-password",
      host="localhost"
  )
  cur = conn.cursor()

  #Generate random seat code
  seat_code = f"A{random.randint(1, 50)}"   # A1–A50

  #Generate random event id
  event_id = random.randint(1, 20)

  try:
    conn.autocommit = False

    #Step 1 reserve seat
    #%s is a generic placeholder for any parameter type. 
    #The driver automatically converts Python values into the correct SQL types.
    cur.execute("""
        INSERT INTO seat_reservation (seat_code, user_id, event_id, expires_at)
        VALUES (%s, %s, %s, NOW() + INTERVAL '10 minutes')
    """, (seat_code, user_id, event_id))

    #Step 2 simulate payment to create ticket
    cur.execute("""
        INSERT INTO tickets (price, user_id, event_id, seat_code)
        VALUES (50, %s, %s, %s)
    """, (user_id, event_id, seat_code))

    # Step 3 remove reservation ONLY after success
    # cur.execute("""
    #     DELETE FROM seat_reservation
    #     WHERE seat_code = %s AND event_id = %s
    # """, (seat_code, event_id))

    conn.commit()
    print(f"User {user_id} booked {seat_code} for event {event_id}")
    print(f" ")

  except Exception as e:
    #In case of an error in the processs undo all the changes
    conn.rollback()
    print(f"User {user_id} failed for {seat_code}, event {event_id}: {e}")
    print(f" ")

  finally:
    cur.close()
    conn.close()


# Simulate 1000 users
threads = []

for i in range(1, 1001):
  t = threading.Thread(target=book_seat, args=(i,))
  threads.append(t)
  t.start()

for t in threads:
  t.join()

print("Simulation completed.")