# Bhavana - Facial Emotion Recognition Chatbot

Bhavana is a web-based chatbot that recognizes a user's facial emotions using the FER2013 model and interacts with them based on their emotions. The chatbot uses the Gemini API to provide personalized responses according to the detected emotion. The website includes several modules like emotion recognition, self-assessment tests, and feedback collection with email confirmations.

## Features

- **Facial Emotion Recognition**: Detects facial emotions through a webcam using the FER2013 model and interacts with users based on their emotions.
- **Chatbot Integration**: A chatbot powered by the Gemini API responds to users according to their detected emotion.
- **Self-Assessment**: Provides stress, anxiety, and depression tests, with doctor recommendations for severe cases.
- **User Authentication**: Includes login and signup functionality, ensuring that each user has a separate chat history.
- **Feedback**: Collects user feedback with a confirmation email sent to the user's email account after submission.
- **MongoDB Integration**: Stores chat history, login/signup details, and feedback in three separate MongoDB collections.

## Project Structure

The project consists of two main folders: `static` and `templates`, along with the main application file `app.py` and `requirements.txt`.

- **static/**: Contains the following subfolders:
  - **CSS**: Stylesheets for the website.
  - **js**: JavaScript files for interactive elements.
  - **images**: Image assets used across the website.
  
- **templates/**: Contains the HTML files for all pages:
  - **home.html**: The homepage of the website.
  - **bhavana.html**: Contains the webcam and chat functionality for emotion recognition.
  - **self_assessment.html**: Provides the self-assessment tests.
  - **about.html**: Information about the project.
  - **feedback.html**: Allows users to submit feedback.
  - **login.html**: The login page.
  - **signup.html**: The signup page.

- **app.py**: The main Flask application that handles routing, webcam access, chatbot integration, and database operations.
- **requirements.txt**: Lists all the Python dependencies needed to run the project.

## MongoDB Collections

The MongoDB database is used to store the following information:

1. **Chat History**: Stores individual chat histories for logged-in users.
2. **Login/Signup Details**: Stores user credentials for authentication.
3. **Feedback**: Stores user feedback along with email confirmations.

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/sukruth30/Facial-emotion-recognition-chatbot.git

2. Navigate to the project directory:

   ```bash
   cd Facial-emotion-recognition-chatbot

3. Install the required dependencies:

   ```bash
   pip install -r requirements.txt

4. Set up a MongoDB database with three collections: chat_history, users, and feedback.

5. Set up environment variables for MongoDB connection and Gemini API keys in your Flask app.

6. Run the application:

   ```bash
   python app.py

7. Access the application at http://localhost:5000

## Usage
- **Try Bhavana**: Go to the "Try Bhavana" module, allow webcam access, and start interacting with the emotion recognition chatbot.
- **Self-Assessment**: Take the stress, anxiety, and depression tests and receive doctor recommendations for severe cases.
- **Feedback**: Submit feedback through the "Feedback" page and receive a confirmation email.

## Technologies used
- **Frontend**: HTML, CSS, JavaScript
- **Backend**: Flask (Python)
- **Emotion Recognition**: FER2013 Model
- **Chatbot**: Gemini API
- **Database**: MongoDB
- **Webcam Integration**: OpenCV
- **Feedback mail server**: SMTP

## License
This project is licensed under the MIT License. See the LICENSE file for more details.

## Acknowledgements
- FER2013 model for emotion recognition.
- Gemini API for powering the chatbot.
- MongoDB for data storage.
- Flask framework for building the web application.
