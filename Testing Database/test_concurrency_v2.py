#This is a python script for testing the postgresql database
#Test to see if the flow is working as expected
import psycopg2
import threading

def book_seat(user_id):
    #Connect to DB
    conn = psycopg2.connect(
        dbname="event-booking-system",
        user="postgres",
        password="database-password",
        host="localhost"
    )
    cur = conn.cursor()

    try:
        conn.autocommit = False

        # Step 1: reserve seat
        cur.execute("""
            INSERT INTO seat_reservation (seat_code, user_id, event_id, expires_at)
            VALUES ('A10', %s, 2, NOW() + INTERVAL '10 minutes')
        """, (user_id,))

        # Step 2: simulate payment → create ticket
        cur.execute("""
            INSERT INTO tickets (price, user_id, event_id, seat_code)
            VALUES (50, %s, 2, 'A10')
        """, (user_id,))

        # Step 3: remove reservation
        cur.execute("""
            DELETE FROM seat_reservation
            WHERE seat_code = 'A10' AND event_id = 1
        """)

        conn.commit()
        print(f"User {user_id} successfully booked seat")

    except Exception as e:
       #undo eveything in the event an error occurs, such as duplication
        conn.rollback()
        print(f"User {user_id} failed:", e)

    finally:
        cur.close()
        conn.close()

# Simulate multiple users
threads = []
for i in range(1, 11):
    t = threading.Thread(target=book_seat, args=(i,))
    threads.append(t)
    t.start()

for t in threads:
    t.join()