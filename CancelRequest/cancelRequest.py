from flask import Flask, request, jsonify
from flask_cors import CORS

import os, sys

import requests
from invokes import invoke_http
app = Flask(__name__)
CORS(app)
sys.path.append('../')
from send_notifications import send_notifications

adoption_URL = "http://localhost:5110/adoptionRequests/{}"



@app.route("/cancel_request", methods=['POST'])
def cancel_request():
    # Simple check of input format and data of the request are JSON

    if request.is_json:
        try:

            request_data = request.get_json().get("request")
            print(request_data)

            print("\nReceived a request in JSON:", request_data)

            # Update adoption status
            adoption_response = invoke_http(adoption_URL.format(request_data.get('requestId')), method='PUT', json={"status": "cancel"})
            print('Adoption response:', adoption_response)

            # Send notification
            notification_response = send_notifications(request_data, "cancel")
            print('Notification response', notification_response)

            # Send cancellation request to booking service
            email = request_data.get('email') 
            cancel_booking_response = invoke_http(
                'http://localhost:5600/process_cancellation',
                method='POST',
                json={'email': email}
            )
            print('Cancel booking response:', cancel_booking_response)
            
            # Update the pet application number
            pet_url = 'http://localhost:8082/remove_applicants/{}'.format(request_data.get('petid'))
            pet_applicant_response = invoke_http(
                pet_url,
                method='PUT'
            )
            print('Update pet applicant number response: ', pet_applicant_response)       

            return jsonify({
                "code": 200,
                "adoption_response": adoption_response,
                "notification_response": notification_response,
                "cancel_booking_response": cancel_booking_response ,
                "pet_applicant_response": pet_applicant_response
            }), 200

        except Exception as e:
            # Unexpected error in code
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            ex_str = str(e) + " at " + str(exc_type) + ": " + fname + ": line " + str(exc_tb.tb_lineno)
            print(ex_str)

            return jsonify({
                "code": 500,
                "message": "place_order.py internal error: " + ex_str
            }), 500

    # if reached here, not a JSON request.
    return jsonify({
        "code": 400,
        "message": "Invalid JSON input: " + str(request.get_data())
    }), 400



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5100, debug=True)
