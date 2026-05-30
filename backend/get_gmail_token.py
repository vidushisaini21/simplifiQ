import sys
import webbrowser
import httpx
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

PORT = 8080
REDIRECT_URI = f"http://localhost:{PORT}"
SCOPES = "https://www.googleapis.com/auth/gmail.send"

print("=========================================================")
print("  SimpliFiQ Gmail API Token Generator")
print("=========================================================")

client_id = input("Enter your OAuth Client ID: ").strip()
client_secret = input("Enter your OAuth Client Secret: ").strip()

if not client_id or not client_secret:
    print("Error: Client ID and Client Secret are required.")
    sys.exit(1)

# Construct Google OAuth Authorization URL
auth_url = (
    "https://accounts.google.com/o/oauth2/v2/auth"
    f"?client_id={client_id}"
    f"&redirect_uri={REDIRECT_URI}"
    "&response_type=code"
    f"&scope={SCOPES}"
    "&access_type=offline"
    "&prompt=consent"
)

print("\n1. Opening browser to authorize your Gmail account...")
print("If the browser doesn't open, copy and paste this URL:")
print(auth_url)

webbrowser.open(auth_url)

code = None

class OAuthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global code
        parsed_path = urlparse(self.path)
        params = parse_qs(parsed_path.query)
        if "code" in params:
            code = params["code"][0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(
                b"<h1>Authorization successful!</h1>"
                b"<p>You can close this browser window and return to your terminal.</p>"
            )
        else:
            self.send_response(400)
            self.end_headers()

    def log_message(self, format, *args):
        # Suppress server logging to keep terminal clean
        return

# Start temporary local HTTP server to capture redirect
server = HTTPServer(("127.0.0.1", PORT), OAuthHandler)
print("\n2. Waiting for authorization code from browser (redirecting)...")
server.handle_request()

if code:
    print("\n3. Exchanging authorization code for tokens...")
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code",
    }
    try:
        response = httpx.post(token_url, data=data)
        res_data = response.json()
        if "refresh_token" in res_data:
            print("\n================== SUCCESS ==================")
            print("Add the following lines to your local .env file")
            print("AND your Render Environment Variables:")
            print("---------------------------------------------")
            print(f"GMAIL_CLIENT_ID={client_id}")
            print(f"GMAIL_CLIENT_SECRET={client_secret}")
            print(f"GMAIL_REFRESH_TOKEN={res_data['refresh_token']}")
            print("=============================================")
        else:
            print("\n================== ERROR ==================")
            print("Failed to get refresh token. Response:")
            print(res_data)
            print("Ensure that your OAuth Client was created as a 'Desktop App'.")
    except Exception as e:
        print(f"\nError exchanging code: {e}")
else:
    print("\nAuthorization failed or timed out.")
