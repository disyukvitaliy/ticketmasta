from flask import Flask, request, make_response
import sys

app = Flask(__name__)

@app.route('/')
def main_page():
    # return 'Main page'
    print(request.environ)
    sys.stdout.flush()
    headers = {key: value for key, value in request.headers.items()}
    return f'Headers: {headers}'

@app.route('/home')
def home_page():
    return 'Home page'

@app.route('/profile')
def profile_page():
    headers_to_include = ['X-User-Id', 'X-User-Email', 'X-User-Role']  # Adjust headers as needed
    headers_text = "\n".join(
        f"{header}: {request.headers.get(header, 'Not Provided')}"
        for header in headers_to_include
    )

    response = make_response(headers_text)
    response.mimetype = "text/plain"
    return response, 200

# app.run(host='0.0.0.0')