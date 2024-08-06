import mysql.connector
from PIL import Image
import io

# Function to create database and tables
def create_tables():
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="mydb",
            database="skin_disease"
        )
        cursor = connection.cursor()

        cursor.execute("DROP TABLE IF EXISTS requests")
        cursor.execute("DROP TABLE IF EXISTS doctors")
        cursor.execute("DROP TABLE IF EXISTS patients")

        # Create table for patient data
        cursor.execute('''CREATE TABLE IF NOT EXISTS PATIENTS(
            P_ID INT AUTO_INCREMENT PRIMARY KEY,
            NAME VARCHAR(255) NOT NULL,
            EMAIL VARCHAR(255) NOT NULL,
            PASSWORD VARCHAR(255) NOT NULL)
        ''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS doctors(
            D_ID INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            email VARCHAR(255) NOT NULL,
            password VARCHAR(255) NOT NULL,
            phone VARCHAR(20))
        ''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS requests(
            I_ID INT AUTO_INCREMENT PRIMARY KEY,
            P_ID INT,
            D_ID INT,
            IMAGE LONGBLOB,
            PREDICTION VARCHAR(255),
            CONFIRMATION_STATUS INT,
            REPLY VARCHAR(10),
            SUGGESTIONS TEXT,
            FOREIGN KEY (P_ID) REFERENCES PATIENTS(P_ID),
            FOREIGN KEY (D_ID) REFERENCES doctors(D_ID)
        )''')

        connection.commit()
        print("Tables created successfully.")
    except mysql.connector.Error as error:
        print("Error creating tables:", error)
    finally:
        cursor.close()
        connection.close()

# Function to populate sample data
def populate_data():
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="mydb",
            database="skin_disease"
        )
        cursor = connection.cursor()

        cursor.execute('''INSERT INTO patients (name, email, password) VALUES 
            ("person1", "p@gmail.com", "password")''')
        cursor.execute('''INSERT INTO doctors (name, email, password) VALUES 
            ("doctor1", "d1@gmail.com", "abc")''')

        connection.commit()
        print("Data populated successfully.")
    except mysql.connector.Error as error:
        print("Error populating data:", error)
    finally:
        cursor.close()
        connection.close()

# Function to check database records
def check():
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="mydb",
            database="skin_disease"
        )
        cursor = connection.cursor()

        cursor.execute("SELECT * FROM patients")
        print("Patients:")
        print(cursor.fetchall())

        cursor.execute("SELECT * FROM doctors")
        print("Doctors:")
        print(cursor.fetchall())

        cursor.execute("SELECT I_ID, P_ID, D_ID, CONFIRMATION_STATUS FROM requests")
        print("Requests:")
        print(cursor.fetchall())
    except mysql.connector.Error as error:
        print("Error checking records:", error)
    finally:
        cursor.close()
        connection.close()

# Function to check login credentials
def login_check(email, password, user_type):
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="mydb",
            database="skin_disease"
        )
        cursor = connection.cursor(dictionary=True)

        if user_type == 'doctor':
            query = "SELECT * FROM doctors WHERE email = %s AND password = %s"
        elif user_type == 'user':
            query = "SELECT * FROM patients WHERE email = %s AND password = %s"
        else:
            return None

        cursor.execute(query, (email, password))
        user = cursor.fetchone()

        connection.commit()
        return user
    except mysql.connector.Error as error:
        print("Error checking login credentials:", error)
        return None
    finally:
        cursor.close()
        connection.close()

# Function to retrieve patient data for analysis by admin (doctor) and convert BLOB to image
def retrieve_and_convert_image(p_id):
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="mydb",
            database="skin_disease"
        )
        cursor = connection.cursor()

        # Query database for patient data
        cursor.execute('''SELECT IMAGE FROM requests WHERE P_ID = %s''', (p_id,))
        image_data = cursor.fetchone()

        # Check if image data is retrieved
        if image_data:
            # Convert binary image data to PIL Image object
            image = Image.open(io.BytesIO(image_data[0]))
            return image
        else:
            print("No patient data found.")
            return None
    except mysql.connector.Error as error:
        print("Error retrieving and converting image:", error)
        return None
    finally:
        cursor.close()
        connection.close()

# Function to update doctor for a new request
def update_doctor_for_new_request(p_id, prediction, image_path):
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="mydb",
            database="skin_disease"
        )
        cursor = connection.cursor()

        with open(image_path, 'rb') as f:
            image_data = f.read()

        # Insert new row into the requests table
        insert_query = "INSERT INTO requests (P_ID, PREDICTION, IMAGE) VALUES (%s, %s, %s)"
        cursor.execute(insert_query, (p_id, prediction, image_data))

        # Get the doctor with the minimum number of associated images in the requests table
        min_doctor_query = """
            SELECT D_ID, COUNT(IMAGE) AS num_requests
            FROM doctors
            LEFT JOIN requests ON requests.D_ID = doctors.D_ID AND requests.CONFIRMATION_STATUS = 0
            GROUP BY doctors.D_ID
            ORDER BY num_requests ASC 
            LIMIT 1
        """

        cursor.execute(min_doctor_query)
        min_doctor = cursor.fetchone()

        if min_doctor:
            cursor.execute("SELECT LAST_INSERT_ID()")
            last_insert_id = cursor.fetchone()[0]

            # Update the doctor_id for the most recent request
            update_query = "UPDATE requests SET D_ID = %s, CONFIRMATION_STATUS = 0 WHERE I_ID = %s"
            cursor.execute(update_query, (min_doctor[0], last_insert_id))

            connection.commit()
            print("Doctor updated for the new request.")
        else:
            print("No doctor found.")
    except mysql.connector.Error as error:
        print("Error updating doctor for new request:", error)
        connection.rollback()
    finally:
        cursor.close()
        connection.close()

# Function to update request details
def update_request_details(i_id, d_id, suggestions, reply):
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="mydb",
            database="skin_disease"
        )
        cursor = connection.cursor()

        # Update the row in the requests table with the provided values
        update_query = """
            UPDATE requests
            SET SUGGESTIONS = %s, REPLY = %s, CONFIRMATION_STATUS = 1 
            WHERE I_ID = %s AND D_ID = %s
        """
        cursor.execute(update_query, (suggestions, reply, i_id, d_id))

        connection.commit()
        print("Request modified successfully.")
    except mysql.connector.Error as error:
        print("Error modifying request:", error)
        connection.rollback()
    finally:
        cursor.close()
        connection.close()

# Function to view requests for a patient
def view_requests_p(p_id):
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="mydb",
            database="skin_disease"
        )
        cursor = connection.cursor()

        query = "SELECT * FROM requests WHERE P_ID = %s"
        cursor.execute(query, (p_id,))
        requests = cursor.fetchall()

        return requests
    except mysql.connector.Error as error:
        print("Error viewing requests:", error)
        return []
    finally:
        cursor.close()
        connection.close()

# Function to view requests for a doctor
def view_requests_d(d_id):
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="mydb",
            database="skin_disease"
        )
        cursor = connection.cursor()

        query = "SELECT * FROM requests WHERE D_ID = %s"
        cursor.execute(query, (d_id,))
        requests = cursor.fetchall()

        return requests
    except mysql.connector.Error as error:
        print("Error viewing requests:", error)
        return []
    finally:
        cursor.close()
        connection.close()

# Example usage
# create_tables()
# populate_data()
# check()
# update_doctor_for_new_request(1, "Some prediction", "actinic-cheilitis-sq-cell-lip-47.jpg")
# update_request_details(1, 10, "Some suggestion", "Some reply")
# requests = view_requests_p(1)
# for request in requests:
#     print(request)
# image = retrieve_and_convert_image(1)
# if image:
#     image.show()
# user = login_check('d1@gmail.com', 'abc', 'doctor')
# print(user)
