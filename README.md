## Eclair modules
- self-ask google search
- google calendar scheduling from chat logs

## Usage
The code is mostly a template at the moment, meant more to be copied/referenced when building Eclair modules.
### Google calendar:
- Follow https://developers.google.com/calendar/api/quickstart/python to eventually get a `credentials.json` file and place it in the project root.
- Install requirements: `pip install -r requirements.txt`
- Import the module in a python file and see the example at the bottom of actions/google_calendar/gcal.py for usage.

### Self-ask google search:
- Install requirements: `pip install -r requirements.txt`
- Install a version of the chromedriver suitable for your chrome version from https://chromedriver.chromium.org/downloads and make sure it is accessible to selenium
- See gsearch_example.py for usage