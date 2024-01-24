from flask import Flask, jsonify, request
from datetime import datetime, timedelta
from functools import wraps
from models import db, RateLimit
from werkzeug.wrappers import Request

request_history = {}

def resend_otp_decorator(message):
    return rate_limit_decorator(limit=1, period=60, message=message)
    
def login_decorator(message):
    return rate_limit_decorator(limit=3, period=60*5, message=message)

def cleanup_expired_ips():
    current_time = datetime.now()
    RateLimit.query.filter(RateLimit.expiration_timestamp < current_time).delete()
    db.session.commit()

def rate_limit_decorator(limit, period, message):
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Clean up expired IP addresses
            cleanup_expired_ips()
            # Get remote_addr
            
            
            ip_address = Request.remote_addr

            print('IP ADD: ', ip_address)

            # Check if the IP address is in the database
            rate_limit_entry = RateLimit.query.filter_by(ip_address=ip_address).first()

            if rate_limit_entry:
                # Entry exists, check for rate limit
                request_count = rate_limit_entry.request_count
                print("LIMIT VALUE: ", request_count)
                print("LAST REQUEST: ", rate_limit_entry.last_request_timestamp)

                # Check if the time difference is within the limit_period
                if datetime.now() - rate_limit_entry.last_request_timestamp < timedelta(seconds=period):
                    # Check if the number of requests is within the limit
                    if request_count >= limit:
                        print("LIMIT REACHED")
                        return jsonify({"error": True, "message": message}), 429
                    else:
                        # Increment the request count
                        rate_limit_entry.request_count += 1
                else:
                    # Reset the request count if the period has passed
                    rate_limit_entry.request_count = 1
                    rate_limit_entry.last_request_timestamp = datetime.now()
            else:
                # Initialize the rate limit entry for a new IP address
                expiration_timestamp = datetime.now() + timedelta(seconds=period)
                rate_limit_entry = RateLimit(ip_address=ip_address, request_count=1, expiration_timestamp=expiration_timestamp)
                db.session.add(rate_limit_entry)

            db.session.commit()

            # Call the original function
            return func(*args, **kwargs)

        return wrapper

    return decorator
