import requests
import boto3
from twilio.rest import  Client
import os
from datetime import datetime, date
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event: any, context: any):
    """
    AWS Lambda handler function to fetch deals, check for new ones, and send notifications.
    """
    try:
        dynamodb = boto3.resource("dynamodb", region_name="eu-north-1")
        table_name = os.environ["TABLE_NAME"]
        table = dynamodb.Table(table_name)

        url = "https://cms.merchantmarketplace.com/api/funding/marketplace/getdeals"
        data = get_deals(url, 15, False)

        check_latest_deal(table, data)
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        send_whatsapp_notiication("The code is having an error please contact the developer to check it out! Thanks!")


def get_deals(site_url: str, page_size: int, first_time_request: bool):
    """
    Fetch deals from the provided API.
    
    Args:
        site_url (str): The API endpoint.
        page_size (int): Number of records per request.
        first_time_request (bool): If it's the initial data fetch.
    
    Returns:
        dict: Contains lists of deal IDs, names, and saved dates.
    """

    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "*/*"
    }

    deal_id_list = []
    deal_name_list = []
    deal_date_list = []

    offset = 0
    limit = page_size

    if first_time_request:
        active = True
        while active:
            body = {
                "offset": offset,
                "limit": limit,
                "filter": None
            }

            response = requests.post(url=site_url, headers=headers, json=body)
            response_details = response.json()
            deals = response_details["data"]
            if deals != []:
                logger.info("Getting deals")
                for deal in deals:
                    deal_id = deal["id"]
                    deal_id_list.append(deal_id)
                    deal_name = deal.get("name", None)
                    deal_name_list.append(deal_name)
                    deal_date = str(date.today())
                    deal_date_list.append(deal_date)

                offset = offset + limit
            else:
                logger.info("No deals found")
                active = False
                break
            logger.info(f"Next offset: {offset}")
    else:
        body = {
            "offset": offset,
            "limit": limit,
            "filter": None
        }

        response = requests.post(url=site_url, headers=headers, json=body)
        response_details = response.json()
        deals = response_details["data"]
        logger.info("Getting data")
        for deal in deals:
            deal_id = deal["id"]
            deal_id_list.append(str(deal_id))
            deal_name = deal.get("name", None)
            deal_name_list.append(deal_name)
            deal_date = str(date.today())
            deal_date_list.append(deal_date)
        logger.info("Done Getting data")

    data = {
        "id": deal_id_list,
        "name": deal_name_list,
        "saved_date": deal_date_list
    }
    logger.info("Done making deal request")

    return data


def get_table_item_count(table_name):
    """
     Retrieve number of data in the database.
    """
    dynamodb = boto3.client("dynamodb", region_name="eu-north-1")
    response = dynamodb.describe_table(TableName=table_name)
    return response["Table"]["ItemCount"]


def get_data_from_database(table, deal_id):
    """
     Retrieve all data from the DynamoDB table.
    """
    response = table.query(
        KeyConditionExpression=boto3.dynamodb.conditions.Key('id').eq(deal_id)
    )
    return response.get('Items', [])


def save_data_into_database(table, data):
    """
    Save new deals into the database in batch mode.
    """

    logger.info("saving data into database")
    # Batch write operation
    with table.batch_writer() as batch:
        for item in data:
            batch.put_item(Item=item)

    logger.info("Done saving new data")


def delete_data_from_database(table, no_of_row):
    """
    Delete old records if the database size exceeds 100,000 entries.
    """

    logger.info("Database size exceeded 100,000! Deleting old records...")
    
    items = []
    last_evaluated_key = None

    while True:
        if last_evaluated_key:
            response = table.scan(ExclusiveStartKey=last_evaluated_key)
        else:
            response = table.scan()

        items.extend(response.get("Items", []))
        last_evaluated_key = response.get("LastEvaluatedKey")

        if not last_evaluated_key:
            break

    items.sort(key=lambda x: datetime.strptime(x.get("saved_date", "2025-02-25"), "%Y-%m-%d"))
    excess = no_of_row - 100000
    old_items = items[:excess]

    logger.info(f"Deleting {excess} old records...")

    with table.batch_writer() as batch:
        for item in old_items:
            batch.delete_item(Key={"id": item["id"], "name": item["name"]})

    logger.info("Old data cleanup completed successfully.")


def send_whatsapp_notiication(message):
    """
    Send a WhatsApp notification via Twilio when a new deal is found.
    """
    
    logger.info("sending whatsapp message")

    sid = os.environ["ACCOUNT_SID"]
    auth_token = os.environ["AUTH_TOKEN"]
    reciever_number = os.environ["RECIEVER_NUMBER"]
    sender_number = os.environ["SENDER_NUMBER"]

    client = Client(sid, auth_token)
    client.messages.create(to=reciever_number, from_=sender_number, body=message)
    logger.info("Message sent")
        

def check_latest_deal(table, data):
    """
    Compare latest fetched deals with the database and notify if there are new deals.
    """

    new_deal_bool = False
    new_deal = []

    latest_requested_data_id = data["id"]
    latest_requested_data_name = data["name"]
    latest_requested_data_date = data["saved_date"]

    for deal_id, deal_name, deal_date in zip(latest_requested_data_id, latest_requested_data_name, latest_requested_data_date):
        existing_data = get_data_from_database(table, deal_id)
        if not existing_data:
            new_deal_bool = True
            new_deal.append({
                'id': deal_id,
                'name': deal_name,
                'saved_date': deal_date
            })

    if new_deal_bool:
        send_whatsapp_notiication("New deal has appeared")
        save_data_into_database(table, new_deal)
    else:
        logger.info("no new deal found")
    
    total_items = get_table_item_count("merchant-market-place-monitor")
    
    if total_items > 100000:
        no_rows = total_items
        delete_data_from_database(table, no_rows)
