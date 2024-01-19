from flask import Flask, jsonify, request
from datetime import datetime, timedelta
from functools import wraps

request_history = {}

def resend_otp_decorator(message):
    return rate_limit_decorator(limit=1, period=60, message=message)
    
def login_decorator(message):
    return rate_limit_decorator(limit=3, period=60*5, message=message)



# Custom rate limiter decorator with dynamic parameters
def rate_limit_decorator(limit, period, message):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            ip_address = request.remote_addr
            print('IP ADD: ', ip_address)
            # Check if the IP address is in the request_history dictionary
            if ip_address in request_history:
                # Get the timestamp of the last request
                last_request_time = request_history[ip_address]

                # Check if the time difference is within the limit_period
                if datetime.now() - last_request_time < timedelta(seconds=period):
                    print("REACH DECORATOR")
                    return jsonify({"error": True, "message": message}), 429

            # Update the request_history with the current timestamp
            request_history[ip_address] = datetime.now()

            # Call the original function
            return func(*args, **kwargs)

        return wrapper

    return decorator