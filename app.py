import os
import numpy as np
from flask import Flask, render_template, request, redirect, url_for,session
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
import tensorflow as tf
from PIL import Image
import mysql.connector
from database.test import *

import base64

# Initialize Flask app
app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
# Load the trained model
model = load_model('vgg16.h5')

# Function to preprocess input image

# Function to preprocess input image
def preprocess_image(image_path):
    try:
        img = Image.open(image_path)
        img = img.resize((256, 256))  # Resize input image to match expected input shape
        img_array = np.array(img)
        img_array = img_array / 255.0  # Normalize pixel values
        img_array = np.expand_dims(img_array, axis=0)  # Add batch dimension
        return img_array
    except Exception as e:
        print("Error processing image:", e)
        return None


# Add logic to interpret prediction and return the disease label
def interpret_prediction(prediction):
    # Define classes
    classes = ['Acne and Rosacea Photos', 'Actinic Keratosis Basal Cell Carcinoma and other Malignant Lesions', 'Melanoma Skin Cancer Nevi and Moles']

    
    score = tf.nn.softmax(prediction[0])
    print(score)
    # Get the index of the class with the highest probability
    predicted_class_index = np.argmax(score)
    print(predicted_class_index)

    # Get the corresponding disease label from the classes list
    disease_label = classes[predicted_class_index]
    probability = score[predicted_class_index].numpy()
    print(disease_label,"ppp: ",probability)
    return disease_label,round(probability*100,2)


# Function to predict disease
def predict_disease(image_path):
    processed_image = preprocess_image(image_path)
    prediction = model.predict(processed_image)
    # Interpret the prediction and return the disease label

    return interpret_prediction(prediction)
     

file_path=""
disease=""
gl_p_id=""
gl_d_id=""

# Combined route for both GET and POST requests
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        return render_template('index.html')
    elif request.method == 'POST':
        # Get file from the form
        file = request.files['file']
        if file:
            # Save file
            file_path = 'uploads/' + file.filename
            file.save(file_path)
            # Predict disease
            global disease
            disease,probability = predict_disease(file)
            # Delete uploaded file
            os.remove(file_path)
            # Return result page with prediction
            return render_template('result.html', disease=disease,probability=probability)
        else:
            return "No file provided"  # Handle no file provided error


@app.route('/predict', methods=['GET', 'POST'])
def predict():
    if request.method == 'GET':
        return render_template('predict.html')
    elif request.method == 'POST':
        # Get file from the form
        global file
        file = request.files['file']
        if file:
            # Save file
            global file_path
            file_path = 'uploads/' + file.filename
            file.save(file_path)
            # Predict disease
            disease,probability = predict_disease(file_path)
            # Delete uploaded file
            #os.remove(file_path)
            # Return result page with prediction
            return render_template('result_after_signin.html', disease=disease,probability=probability)
        else:
            return "No file provided"  # Handle no file provided error

@app.route('/consult', methods=['GET', 'POST'])
def consult():

    """ if file_path:
        # Save file
        #file_path = 'uploads/' + file.filename
        file.save(file_path)
        #disease,probability = predict_disease(file_path)
    else:
        print("file empty")  

    update_doctor_for_new_request(gl_p_id, disease, file_path)  """ 
    return render_template("consult.html")
        


@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user_type = request.form['user_type']
    
        # Initialize database connection and cursor
        if user_type == 'doctor':
            query = "SELECT D_ID FROM DOCTORS WHERE EMAIL = %s AND PASSWORD = %s"
        elif user_type == 'user':
            query = "SELECT P_ID FROM PATIENTS WHERE EMAIL = %s AND PASSWORD = %s"
        else:
            return render_template('signin.html', error='Invalid user type')
    
        try:
            # Connect to the database
            connection = mysql.connector.connect(
                host="localhost",
                user="root",
                password="mydb",
                database="skin_disease"
            )
            cursor = connection.cursor(dictionary=True)

            # Execute query to check user credentials
            cursor.execute(query, (email, password))
            user = cursor.fetchone()

            connection.commit()
    
            if user:
                # Store P_ID in session
                if user_type=='user':
                    global gl_p_id
                    gl_p_id=user['P_ID']
                else:
                    global gl_d_id
                    gl_d_id=user['D_ID']
                """ 
                session['P_ID'] = user['P_ID'] if user_type == 'user' else user['D_ID'] """

                # Redirect user based on user type
                if user_type == 'user':
                    return redirect('/predict')
                elif user_type == 'doctor':
                    return redirect('/doctor_dashboard')
            else:
                return render_template('signin.html', error='Invalid email or password')
    
        except mysql.connector.Error as e:
            # Handle database errors
            error_message = 'Database error {}: {}'.format(e.errno, e.msg)
            return render_template('signin.html', error=error_message)
        finally:
            # Close database connection
            if 'conn' in locals() and connection.is_connected():
                cursor.close()
                connection.close()

    return render_template('signin.html')




@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        try:
            # Connect to the database
            connection = mysql.connector.connect(
                host="localhost",
                user="root",
                password="mydb",
                database="skin_disease"
            )
            cursor = connection.cursor(dictionary=True)

            # Check if email already exists in the database
            query = "SELECT * FROM PATIENTS WHERE EMAIL = %s"
            cursor.execute(query, (email,))
            existing_user = cursor.fetchone()

            if existing_user:
                # Email already exists, display error message
                return render_template('signup.html', error='Email already exists. Please choose another one.')

            # Execute INSERT query to add user to the PATIENTS table
            insert_query = "INSERT INTO PATIENTS (NAME, EMAIL, PASSWORD) VALUES (%s, %s, %s)"
            cursor.execute(insert_query, (name, email, password))
            connection.commit()

            # Redirect to sign-in page after successful sign-up
            return redirect('/signin')

        except mysql.connector.Error as e:
            # Handle database errors
            error_message = 'Database error {}: {}'.format(e.errno, e.msg)
            return render_template('signup.html', error=error_message)

        finally:
            # Close database connection
            if 'conn' in locals() and connection.is_connected():
                cursor.close()
                connection.close()

    return render_template('signup.html')


@app.route('/doctor_dashboard')
def doctor_dashboard():
    requests = view_requests_d(1)
    for request in requests:
        encoded_image = Image.open(io.BytesIO(request[3]))
        img = encoded_image.convert("RGB")  # Ensure the image is in RGB mode
        jpeg_bytes = io.BytesIO()
        img.save(jpeg_bytes, format='JPEG')
        jpeg_bytes.seek(0) 
        encoded_image = base64.b64encode(jpeg_bytes.getvalue()).decode('utf-8')
        request=request+(encoded_image,)
        print(request)
    return render_template('doctor_dashboard.html', requests=requests)

""" @app.route('/request',methods=['GET','POST'])
def request():
    if request.method=='GET':
        # Fetch request details from the database based on the request_id
        request_details = view_requests_d(1)
        return render_template('request.html', request=request_details)
    if request.method == 'POST':
        reply = request.form.get('reply')
        suggestions = request.form.get('suggestions')
        update_request_details(1, reply, suggestions)
        return redirect(url_for('doctor_dashboard')) """


if __name__ == '__main__':
    app.run(debug=True)
