"""One-time: get a YouTube refresh token. Run on your own computer.

python3 pipeline/oauth_once.py CLIENT_ID CLIENT_SECRET
Uses only the standard library. Opens the browser, catches the redirect on localhost.
"""
import http.server
import json
import secrets
import sys
import urllib.parse
import urllib.request
import webbrowser

SCOPES = "https://www.googleapis.com/auth/youtube.upload https://www.googleapis.com/auth/youtube.force-ssl"
PORT = 8765


def main():
    cid, csec = sys.argv[1], sys.argv[2]
    redirect = f"http://127.0.0.1:{PORT}"
    state = secrets.token_urlsafe(16)
    url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode({
        "client_id": cid, "redirect_uri": redirect, "response_type": "code", "scope": SCOPES,
        "access_type": "offline", "prompt": "consent", "state": state})
    code_box = {}

    class H(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            if q.get("state", [""])[0] == state and "code" in q:
                code_box["code"] = q["code"][0]
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Done. You can close this tab.")

        def log_message(self, *a):
            pass

    print("Opening browser for consent...")
    webbrowser.open(url)
    srv = http.server.HTTPServer(("127.0.0.1", PORT), H)
    while "code" not in code_box:
        srv.handle_request()
    data = urllib.parse.urlencode({"code": code_box["code"], "client_id": cid, "client_secret": csec,
                                   "redirect_uri": redirect, "grant_type": "authorization_code"}).encode()
    tok = json.load(urllib.request.urlopen("https://oauth2.googleapis.com/token", data))
    print("\nYT_REFRESH_TOKEN =", tok.get("refresh_token", "(none returned, run again)"))


if __name__ == "__main__":
    main()
