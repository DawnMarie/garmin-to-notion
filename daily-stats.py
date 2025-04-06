from datetime import date
from garminconnect import Garmin
from notion_client import Client
from dotenv import load_dotenv
import os


def get_training_status(garmin):
    status_data = garmin.get_training_status(date.today().isoformat())
    most_recent = status_data.get("mostRecentTrainingStatus")\
        .get("latestTrainingStatusData")\
        .get("3485195778")\
        .get("trainingStatusFeedbackPhrase")
    daily_status = most_recent.split("_")[0].capitalize()

    training_readiness = garmin.get_training_readiness(date.today().isoformat())
    score = training_readiness[0].get("score")
    description = training_readiness[0].get("feedbackShort").replace("_", " ").capitalize()

    return daily_status, score, description


def add_daily_status(client, database_id, daily_status, score, description):
    """
    Check if daily status already exists in the Notion database.
    """
    query = client.databases.query(
        database_id=database_id,
        filter={
            "and": [
                {"property": "Today's Date", "date": {"equals": date.today().isoformat()}},
                {"property": "Training Status", "title": {"equals": daily_status}}
            ]
        }
    )
    results = query['results']

    if not results:
        """
        Add a daily status entry in the database
        """
        properties = {
            "Training Status": {"title": [{"text": {"content": daily_status}}]},
            "Today's Date": {"date": {"start": date.today().isoformat()}},
            "Readiness Score": {"rich_text": [{"text": {"content": score}}]},
            "Readiness Description": {"rich_text": [{"text": {"content": description}}]}
        }

        page = {
            "parent": {"database_id": database_id},
            "properties": properties,
        }

        client.pages.create(**page)


def main():
    load_dotenv()

    # Initialize Garmin and Notion clients using environment variables
    garmin_email = os.getenv("GARMIN_EMAIL")
    garmin_password = os.getenv("GARMIN_PASSWORD")
    notion_token = os.getenv("NOTION_TOKEN")
    database_id = os.getenv("NOTION_STATS_DB_ID")

    # Initialize Garmin client and login
    garmin = Garmin(garmin_email, garmin_password)
    garmin.login()
    client = Client(auth=notion_token)

    daily_status, score, description = get_training_status(garmin)

    add_daily_status(client, database_id, daily_status, str(score), description)


if __name__ == '__main__':
    main()
