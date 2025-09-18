# Running

Prerequisites:
- Python (3.10 or newer).
- [Poetry](https://python-poetry.org/docs/#installing-with-pipx)

After cloning the repository:
- `poetry install`
- `poe migrate`
- `poe start`

# instrukcja powrotu do developmentu

## Shorts analytics token
`google.auth.exceptions.RefreshError: ('invalid_grant: Bad Request', {'error': 'invalid_grant', 'error_description': 'Bad Request'})`
remove `token.json`, normally it should refresh token, but i guess refresh token expired as well and it throws, remove token and log in again

## Reels analytics token
`Error: 400
{"error":{"message":"Error validating access token: Session has expired on Wednesday, 26-Mar-25 18:30:47 PDT. The current time is Thursday, 18-Sep-25 08:43:18 PDT.","type":"OAuthException","code":190,"fbtrace_id":"AEkJhbJJCZEFYuuC-zKWOPC"}}`

need new access token. todo for future, figure out refresh token stuff with fb apps. go to `developers.facebook.com/`, your app pushing content, and generate new token